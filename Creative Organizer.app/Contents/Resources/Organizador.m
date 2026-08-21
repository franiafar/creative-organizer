#import <Cocoa/Cocoa.h>

typedef NS_ENUM(NSInteger, OrganizerAction) {
    OrganizerActionOrganize,
    OrganizerActionPreview,
    OrganizerActionUndo,
    OrganizerActionCancel,
};

static void ShowMessage(NSString *title, NSString *message) {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = title;
    alert.informativeText = message;
    [alert addButtonWithTitle:@"Cerrar"];
    [alert runModal];
}

static NSURL *ChooseLaunchFolder(void) {
    NSOpenPanel *panel = [NSOpenPanel openPanel];
    panel.title = @"Organizador de Lanzamientos";
    panel.message = @"Elegi la carpeta del lanzamiento";
    panel.prompt = @"Elegir carpeta";
    panel.canChooseFiles = NO;
    panel.canChooseDirectories = YES;
    panel.canCreateDirectories = NO;
    panel.allowsMultipleSelection = NO;
    panel.directoryURL = [[NSFileManager defaultManager] URLsForDirectory:NSDesktopDirectory inDomains:NSUserDomainMask].firstObject;
    [panel center];
    return [panel runModal] == NSModalResponseOK ? panel.URL : nil;
}

static OrganizerAction ChooseAction(void) {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"Organizador de Lanzamientos";
    alert.informativeText = @"Que queres hacer?";
    [alert addButtonWithTitle:@"Ordenar"];
    [alert addButtonWithTitle:@"Preview"];
    [alert addButtonWithTitle:@"Deshacer el ordenamiento anterior"];
    [alert addButtonWithTitle:@"Salir"];

    switch ([alert runModal]) {
        case NSAlertFirstButtonReturn: return OrganizerActionOrganize;
        case NSAlertSecondButtonReturn: return OrganizerActionPreview;
        case NSAlertThirdButtonReturn: return OrganizerActionUndo;
        default: return OrganizerActionCancel;
    }
}

static NSScrollView *PreviewView(NSString *output) {
    NSRect frame = NSMakeRect(0, 0, 760, 420);
    NSScrollView *scrollView = [[NSScrollView alloc] initWithFrame:frame];
    scrollView.hasVerticalScroller = YES;
    scrollView.hasHorizontalScroller = YES;
    scrollView.autohidesScrollers = YES;
    scrollView.borderType = NSBezelBorder;

    NSTextView *textView = [[NSTextView alloc] initWithFrame:frame];
    textView.editable = NO;
    textView.selectable = YES;
    textView.font = [NSFont monospacedSystemFontOfSize:11 weight:NSFontWeightRegular];
    textView.string = output.length ? output : @"No se detectaron movimientos.";
    textView.minSize = NSMakeSize(0, frame.size.height);
    textView.maxSize = NSMakeSize(CGFLOAT_MAX, CGFLOAT_MAX);
    textView.verticallyResizable = YES;
    textView.horizontallyResizable = YES;
    textView.textContainer.containerSize = NSMakeSize(CGFLOAT_MAX, CGFLOAT_MAX);
    textView.textContainer.widthTracksTextView = NO;
    scrollView.documentView = textView;
    return scrollView;
}

static void ShowPreview(NSString *output) {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"Preview del ordenamiento";
    alert.informativeText = @"Revisa las rutas propuestas. No se movio ningun archivo.";
    alert.accessoryView = PreviewView(output);
    [alert addButtonWithTitle:@"Cerrar"];
    [alert runModal];
}

static BOOL ConfirmPlan(NSString *output) {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"Confirmar ordenamiento";
    alert.informativeText = @"Revisa el plan completo antes de mover archivos.";
    alert.accessoryView = PreviewView(output);
    [alert addButtonWithTitle:@"Ordenar"];
    [alert addButtonWithTitle:@"Cancelar"];
    return [alert runModal] == NSAlertFirstButtonReturn;
}

static NSURL *LastLaunchRecordURL(void) {
    NSError *error = nil;
    NSURL *supportURL = [[NSFileManager defaultManager] URLForDirectory:NSApplicationSupportDirectory inDomain:NSUserDomainMask appropriateForURL:nil create:YES error:&error];
    if (!supportURL) return nil;

    NSURL *folderURL = [supportURL URLByAppendingPathComponent:@"Organizador de Lanzamientos" isDirectory:YES];
    if (![[NSFileManager defaultManager] createDirectoryAtURL:folderURL withIntermediateDirectories:YES attributes:nil error:&error]) {
        return nil;
    }
    return [folderURL URLByAppendingPathComponent:@"last-launch.txt"];
}

static BOOL SaveLastLaunchFolder(NSURL *folder) {
    NSURL *recordURL = LastLaunchRecordURL();
    if (!recordURL) return NO;
    return [folder.path writeToURL:recordURL atomically:YES encoding:NSUTF8StringEncoding error:nil];
}

static NSURL *LoadLastLaunchFolder(void) {
    NSURL *recordURL = LastLaunchRecordURL();
    if (!recordURL) return nil;
    NSString *path = [NSString stringWithContentsOfURL:recordURL encoding:NSUTF8StringEncoding error:nil];
    if (!path.length) return nil;

    BOOL isDirectory = NO;
    if (![[NSFileManager defaultManager] fileExistsAtPath:path isDirectory:&isDirectory] || !isDirectory) {
        return nil;
    }
    return [NSURL fileURLWithPath:path];
}

static void ClearLastLaunchFolder(void) {
    NSURL *recordURL = LastLaunchRecordURL();
    if (recordURL) {
        [[NSFileManager defaultManager] removeItemAtURL:recordURL error:nil];
    }
}

static NSDictionary *RunOrganizer(NSURL *folder, NSString *flag) {
    NSURL *resourcesURL = [NSBundle mainBundle].resourceURL;
    NSString *script = [resourcesURL URLByAppendingPathComponent:@"ordenar_lanzamiento.py"].path;
    NSURL *pythonURL = [resourcesURL URLByAppendingPathComponent:@"Python3.framework/Versions/Current/bin/python3"];
    if (!script || ![[NSFileManager defaultManager] isExecutableFileAtPath:pythonURL.path]) {
        return @{@"success": @NO, @"output": @"No encontre el archivo interno del organizador."};
    }

    NSTask *task = [[NSTask alloc] init];
    NSPipe *pipe = [NSPipe pipe];
    // Python travels inside the app, so teammates do not need Xcode or Python installed.
    task.executableURL = pythonURL;
    task.arguments = @[script, @"--root", folder.path, flag];
    task.standardOutput = pipe;
    task.standardError = pipe;

    NSError *error = nil;
    if (![task launchAndReturnError:&error]) {
        return @{@"success": @NO, @"output": error.localizedDescription ?: @"No pude ejecutar el organizador."};
    }
    NSData *data = [pipe.fileHandleForReading readDataToEndOfFile];
    [task waitUntilExit];
    NSString *output = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
    output = [output stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    return @{@"success": @(task.terminationStatus == 0), @"output": output ?: @""};
}

static NSString *MarketsFromOutput(NSString *output) {
    for (NSString *line in [output componentsSeparatedByString:@"\n"]) {
        if ([line hasPrefix:@"Mercados detectados:"]) {
            return line;
        }
    }
    return @"Mercados detectados: ninguno";
}

int main(void) {
    @autoreleasepool {
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
        [NSApp activateIgnoringOtherApps:YES];

        OrganizerAction action = ChooseAction();
        if (action == OrganizerActionCancel) return 0;

        if (action == OrganizerActionUndo) {
            NSURL *folder = LoadLastLaunchFolder();
            if (!folder) {
                ClearLastLaunchFolder();
                ShowMessage(@"No hay un ordenamiento para deshacer", @"Organiza una carpeta primero. La app solo puede deshacer el ultimo ordenamiento hecho desde esta app.");
                return 0;
            }
            NSDictionary *result = RunOrganizer(folder, @"--undo");
            if ([result[@"success"] boolValue] || [result[@"output"] containsString:@"No encontre un undo"]) {
                ClearLastLaunchFolder();
            }
            ShowMessage([result[@"success"] boolValue] ? @"Undo aplicado" : @"No se pudo hacer Undo", [result[@"success"] boolValue] ? @"La carpeta volvio al estado anterior." : result[@"output"]);
            return 0;
        }

        NSURL *folder = ChooseLaunchFolder();
        if (!folder) return 0;

        NSDictionary *preview = RunOrganizer(folder, @"--preview");
        if (![preview[@"success"] boolValue]) {
            ShowMessage(@"No se pudo generar el preview", preview[@"output"]);
            return 0;
        }
        if (action == OrganizerActionPreview) {
            ShowPreview(preview[@"output"]);
            return 0;
        }
        if (!ConfirmPlan(preview[@"output"])) return 0;

        NSDictionary *result = RunOrganizer(folder, @"--apply");
        if ([result[@"success"] boolValue]) {
            SaveLastLaunchFolder(folder);
        }
        NSString *message = [result[@"success"] boolValue] ? [NSString stringWithFormat:@"Listo. %@", MarketsFromOutput(result[@"output"])] : result[@"output"];
        ShowMessage([result[@"success"] boolValue] ? @"Organizacion terminada" : @"No se pudo ordenar", message);
    }
    return 0;
}
