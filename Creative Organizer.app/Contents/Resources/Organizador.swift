import Cocoa

enum OrganizerAction {
    case organize
    case preview
    case undo
}

func showMessage(title: String, message: String) {
    let alert = NSAlert()
    alert.messageText = title
    alert.informativeText = message
    alert.addButton(withTitle: "Cerrar")
    alert.runModal()
}

func chooseLaunchFolder() -> URL? {
    let panel = NSOpenPanel()
    panel.title = "Organizador de Lanzamientos"
    panel.message = "Elegi la carpeta del lanzamiento"
    panel.prompt = "Elegir carpeta"
    panel.canChooseFiles = false
    panel.canChooseDirectories = true
    panel.canCreateDirectories = false
    panel.allowsMultipleSelection = false
    panel.directoryURL = FileManager.default.urls(for: .desktopDirectory, in: .userDomainMask).first
    panel.center()

    return panel.runModal() == .OK ? panel.url : nil
}

func chooseAction(folderName: String) -> OrganizerAction? {
    let alert = NSAlert()
    alert.messageText = folderName
    alert.informativeText = "Que queres hacer con esta carpeta?"
    alert.addButton(withTitle: "Ordenar")
    alert.addButton(withTitle: "Preview")
    alert.addButton(withTitle: "Undo")
    alert.addButton(withTitle: "Cancelar")

    switch alert.runModal() {
    case .alertFirstButtonReturn: return .organize
    case .alertSecondButtonReturn: return .preview
    case .alertThirdButtonReturn: return .undo
    default: return nil
    }
}

func confirm(title: String, message: String, button: String) -> Bool {
    let alert = NSAlert()
    alert.messageText = title
    alert.informativeText = message
    alert.addButton(withTitle: button)
    alert.addButton(withTitle: "Cancelar")
    return alert.runModal() == .alertFirstButtonReturn
}

func runOrganizer(root: URL, flag: String) -> (success: Bool, output: String) {
    guard let scriptURL = Bundle.main.resourceURL?.appendingPathComponent("ordenar_lanzamiento.py") else {
        return (false, "No encontre el archivo interno del organizador.")
    }

    let process = Process()
    let outputPipe = Pipe()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
    process.arguments = [scriptURL.path, "--root", root.path, flag]
    process.standardOutput = outputPipe
    process.standardError = outputPipe

    do {
        try process.run()
        process.waitUntilExit()
        let data = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return (process.terminationStatus == 0, output)
    } catch {
        return (false, "No pude ejecutar el organizador: \(error.localizedDescription)")
    }
}

func summary(from output: String) -> String {
    let lines = output.split(separator: "\n").filter {
        $0.hasPrefix("Carpeta:") ||
        $0.hasPrefix("Archivos detectados:") ||
        $0.hasPrefix("Archivos listos para mover:") ||
        $0.hasPrefix("Archivos sin resolver:") ||
        $0.hasPrefix("Mercados detectados:")
    }
    return lines.isEmpty ? output : lines.joined(separator: "\n")
}

let app = NSApplication.shared
app.setActivationPolicy(.regular)
app.activate(ignoringOtherApps: true)

guard let folder = chooseLaunchFolder() else {
    app.terminate(nil)
    exit(0)
}

guard let action = chooseAction(folderName: folder.lastPathComponent) else {
    app.terminate(nil)
    exit(0)
}

switch action {
case .preview:
    let result = runOrganizer(root: folder, flag: "--preview")
    showMessage(title: result.success ? "Preview" : "No se pudo hacer el preview", message: summary(from: result.output))

case .undo:
    if confirm(title: "Deshacer organizacion", message: "Esto revierte la ultima organizacion hecha en esta carpeta.", button: "Deshacer") {
        let result = runOrganizer(root: folder, flag: "--undo")
        showMessage(title: result.success ? "Undo aplicado" : "No se pudo hacer Undo", message: result.success ? "La carpeta volvio al estado anterior." : result.output)
    }

case .organize:
    let preview = runOrganizer(root: folder, flag: "--preview")
    guard preview.success else {
        showMessage(title: "No se pudo leer la carpeta", message: preview.output)
        break
    }
    let message = summary(from: preview.output) + "\n\nVoy a mover y renombrar archivos dentro de esta carpeta, sin duplicarlos."
    if confirm(title: "Confirmar organizacion", message: message, button: "Ordenar") {
        let result = runOrganizer(root: folder, flag: "--apply")
        showMessage(title: result.success ? "Organizacion terminada" : "No se pudo ordenar", message: result.success ? "Listo. Los archivos fueron reordenados sin duplicarse." : result.output)
    }
}

app.terminate(nil)
