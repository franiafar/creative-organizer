import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]
ENGINE_PATH = REPOSITORY / "Creative Organizer.app/Contents/Resources/ordenar_lanzamiento.py"
SPEC = importlib.util.spec_from_file_location("creative_organizer_engine", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ENGINE
SPEC.loader.exec_module(ENGINE)


class OrganizerEngineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "Launch with its own name"
        self.root.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def make(self, relative, content=b"asset"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def plan(self, requested_order=None):
        return ENGINE.build_plan(self.root, requested_order)

    def destination_set(self, moves):
        return {move["relativeDestination"] for move in moves}

    def file_snapshot(self):
        return {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

    def directory_snapshot(self):
        return {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_dir() and ".launch-organizer" not in path.parts
        }

    def test_butnow_static_and_motion_share_enriched_creative(self):
        self.make(
            "Meta/Regions/Brazil/Portuguese/Wrestling/Stills/9x16/"
            "Wrestling_ButNow_BRPT_Meta_Still_9x16.jpg"
        )
        self.make(
            "Meta/Regions/Brazil/Portuguese/Wrestling/Video/Motion 11/9x16/"
            "Wrestling_ButNow_BRPT_Meta_Video_15s_9x16.mp4"
        )

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(unresolved)
        self.assertEqual(
            self.destination_set(moves),
            {
                "1 - BR/Static/Wrestling - ButNow/Wrestling_ButNow_BRPT_Meta_Still_9x16.jpg",
                "1 - BR/Motion/Wrestling - ButNow/Wrestling_ButNow_BRPT_Meta_Video_15s_9x16.mp4",
            },
        )

    def test_full_single_type_suffixes_and_no_zero_padding(self):
        self.make("Meta/Brazil/Alpha/Stills/Alpha_BRPT_Meta_Still.jpg")
        self.make("TikTok/Argentina/Beta/Video/Beta_ARES_TT_Video.mp4")

        _, moves, unresolved, _ = self.plan([("BR", None), ("AR", None)])

        self.assertFalse(unresolved)
        destinations = self.destination_set(moves)
        self.assertIn("1 - BR - Static/Alpha/Alpha_BRPT_Meta_Still.jpg", destinations)
        self.assertIn("2 - AR - Motion/Beta/Beta_ARES_TT_Video.mp4", destinations)
        self.assertFalse(any(destination.startswith("0") for destination in destinations))

    def test_multilingual_india_and_canada_labels(self):
        fixtures = [
            "Meta/India/English/Idea/Stills/Idea_INEN_Meta_Still.jpg",
            "Meta/India/Hindi/Idea/Stills/Idea_INHI_Meta_Still.jpg",
            "Meta/India/Roman Hindi/Idea/Stills/Idea_INRO_Meta_Still.jpg",
            "Meta/Canada/English/Idea/Stills/Idea_CAEN_Meta_Still.jpg",
            "Meta/Canada/French Canadian/Idea/Stills/Idea_CAFR_Meta_Still.jpg",
        ]
        for fixture in fixtures:
            self.make(fixture)

        _, moves, unresolved, _ = self.plan(
            [("IN", "EN"), ("IN", "HI"), ("IN", "RO"), ("CA", "EN"), ("CA", "FR")]
        )

        self.assertFalse(unresolved)
        market_folders = {move["relativeDestination"].split("/")[0] for move in moves}
        self.assertEqual(
            market_folders,
            {
                "1 - IN EN - Static",
                "2 - IN HI - Static",
                "3 - IN RO - Static",
                "4 - CA EN - Static",
                "5 - CA FR - Static",
            },
        )

    def test_arbitrary_semantic_hierarchy_before_and_after_media_is_preserved(self):
        self.make(
            "Meta/Brazil/Hair Analysis/Stills/Hair Analysis CTA/Hook A/"
            "Hair_Analysis_CTA_Hook_A_BRPT_Meta_Still.jpg"
        )
        self.make(
            "Meta/Brazil/Hair Analysis/Video/Hair Analysis CTA Alt/Character B/"
            "Hair_Analysis_CTA_Alt_Character_B_BRPT_Meta_Video.mp4"
        )

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(unresolved)
        destinations = self.destination_set(moves)
        self.assertTrue(any("Hair Analysis/Hair Analysis CTA/Hook A" in path for path in destinations))
        self.assertTrue(any("Hair Analysis/Hair Analysis CTA Alt/Character B" in path for path in destinations))

    def test_source_path_outranks_conflicting_filename_and_keeps_test_siblings_separate(self):
        self.make(
            "Meta/Brazil/Hairstyle/Test A/Stills/Personal_Color_Analysis_BRPT_Meta_Still.jpg",
            b"hair",
        )
        self.make(
            "Meta/Brazil/Color Analysis/Test A/Stills/Personal_Color_Analysis_BRPT_Meta_Still.jpg",
            b"color",
        )

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(unresolved)
        destinations = self.destination_set(moves)
        self.assertTrue(any("/Hairstyle/Test A/" in path for path in destinations))
        self.assertTrue(any("/Color Analysis/Test A/" in path for path in destinations))

    def test_filename_only_fallback_is_shared_for_static_and_motion_and_human_readable(self):
        self.make("Meta/BRPT/Stills/Something_To_Wear_BRPT_Meta_Still_4x5.jpg")
        self.make("Meta/BRPT/Video/Something_To_Wear_BRPT_Meta_Video_9x16.mp4")

        records, moves, unresolved, _ = self.plan()

        self.assertFalse(unresolved)
        self.assertEqual({record.creative_name for record in records}, {"Something To Wear"})
        self.assertEqual({move["confidence"] for move in moves}, {"medium"})
        self.assertTrue(all("Something To Wear" in path for path in self.destination_set(moves)))

    def test_meta_tiktok_coexist_without_platform_level_and_youtube_sheet_stay_untouched(self):
        meta = self.make("Meta/Brazil/Concept/Stills/Concept_BRPT_Meta_Still_4x5.jpg", b"meta")
        tiktok = self.make("TikTok/Brazil/Concept/Stills/Concept_BRPT_TT_Still_9x16.jpg", b"tt")
        youtube = self.make("YouTube/Brazil/Concept/Video/Concept_BRPT_YouTube_Video.mp4", b"yt")
        sheet = self.make("traffic.xlsx", b"sheet")
        empty_youtube_folder = self.root / "YouTube/Empty delivery"
        empty_youtube_folder.mkdir(parents=True)

        _, moves, unresolved, summary = self.plan()
        ENGINE.apply_plan(self.root, moves, unresolved, summary["systemJunk"])

        destinations = self.destination_set(moves)
        self.assertFalse(any("/Meta/" in destination or "/TikTok/" in destination for destination in destinations))
        self.assertFalse(meta.exists())
        self.assertFalse(tiktok.exists())
        self.assertEqual(youtube.read_bytes(), b"yt")
        self.assertEqual(sheet.read_bytes(), b"sheet")
        self.assertTrue(empty_youtube_folder.is_dir())
        self.assertFalse((self.root / "Otros").exists())

    def test_asymmetric_platform_availability_builds_only_observed_folders(self):
        self.make("Meta/Brazil/Only Meta/Stills/Only_Meta_BRPT_Meta_Still.jpg")
        self.make("TikTok/Brazil/Both/Stills/Both_BRPT_TT_Still.jpg")
        self.make("Meta/Brazil/Both/Stills/Both_BRPT_Meta_Still.jpg")

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(unresolved)
        destinations = self.destination_set(moves)
        self.assertTrue(any("/Only Meta/" in destination and "/Meta/" not in destination for destination in destinations))
        self.assertEqual(sum("/Both/" in destination for destination in destinations), 2)

    def test_cross_platform_name_collision_adds_platform_level(self):
        self.make("Meta/Brazil/Concept/Stills/Same_Name_BRPT_Meta_Still.jpg", b"meta")
        self.make("TikTok/Brazil/Concept/Stills/Same_Name_BRPT_Meta_Still.jpg", b"tiktok")

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(unresolved)
        self.assertEqual(
            self.destination_set(moves),
            {
                "1 - BR - Static/Meta/Concept/Same_Name_BRPT_Meta_Still.jpg",
                "1 - BR - Static/TikTok/Concept/Same_Name_BRPT_Meta_Still.jpg",
            },
        )

    def test_same_platform_collision_and_identical_duplicate_remain_unmoved(self):
        first = self.make("Meta/Brazil/Concept/Stills/4x5/Same_BRPT_Meta_Still.jpg", b"identical")
        second = self.make("Meta/Brazil/Concept/Stills/9x16/Same_BRPT_Meta_Still.jpg", b"identical")

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(moves)
        self.assertEqual(len(unresolved), 2)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())

    def test_existing_byte_identical_destination_is_preserved_not_deleted(self):
        source = self.make("Meta/Brazil/Concept/Stills/Same_BRPT_Meta_Still.jpg", b"same")
        existing = self.make("1 - BR - Static/Concept/Same_BRPT_Meta_Still.jpg", b"same")

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(moves)
        self.assertTrue(unresolved)
        self.assertTrue(source.exists())
        self.assertTrue(existing.exists())

    def test_existing_nonidentical_destination_collision_is_unresolved(self):
        source = self.make("Meta/Brazil/Concept/Stills/Same_BRPT_Meta_Still.jpg", b"new")
        existing = self.make("1 - BR - Static/Concept/Same_BRPT_Meta_Still.jpg", b"old")

        _, moves, unresolved, _ = self.plan()

        self.assertFalse(moves)
        self.assertEqual(len(unresolved), 2)
        self.assertEqual(source.read_bytes(), b"new")
        self.assertEqual(existing.read_bytes(), b"old")

    def test_unresolved_platform_evidence_leaves_file_unmoved(self):
        asset = self.make("Brazil/Concept/Stills/Concept_BRPT_Still.jpg")

        _, moves, unresolved, summary = self.plan()

        self.assertFalse(moves)
        self.assertEqual(len(unresolved), 1)
        self.assertIn("No supported Meta or TikTok platform evidence", unresolved[0].reasons)
        self.assertEqual(summary["unresolvedFiles"], 1)
        self.assertTrue(asset.exists())

    def test_preview_lists_complete_evidence_and_does_no_writes(self):
        self.make("Meta/Brazil/Concept/Stills/Concept_BRPT_Meta_Still.jpg")
        before_files = self.file_snapshot()
        before_directories = self.directory_snapshot()

        records, moves, unresolved, summary = self.plan()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            ENGINE.print_summary(self.root, summary, moves, unresolved)

        self.assertEqual(before_files, self.file_snapshot())
        self.assertEqual(before_directories, self.directory_snapshot())
        self.assertFalse((self.root / ".launch-organizer").exists())
        self.assertIn("relativeDestination", moves[0])
        self.assertIn("evidence", moves[0])
        self.assertIn("ignoredMetadata", moves[0])
        self.assertIn("confidence", moves[0])
        self.assertIn("Concept_BRPT_Meta_Still.jpg", output.getvalue())
        self.assertEqual(len(records), 1)

    def test_apply_second_run_is_idempotent_and_undo_restores_original_tree(self):
        original = self.make("Meta/Brazil/Concept/Stills/Concept_BRPT_Still.jpg", b"original")
        original_files = self.file_snapshot()
        original_directories = self.directory_snapshot()
        _, moves, unresolved, summary = self.plan()
        undo_path = ENGINE.apply_plan(self.root, moves, unresolved, summary["systemJunk"])
        organized_files = self.file_snapshot()

        _, second_moves, second_unresolved, second_summary = self.plan()
        self.assertFalse(second_unresolved)
        self.assertEqual({move["action"] for move in second_moves}, {"stay"})
        second_undo = ENGINE.apply_plan(
            self.root, second_moves, second_unresolved, second_summary["systemJunk"]
        )
        self.assertEqual(undo_path, second_undo)
        self.assertEqual(organized_files, self.file_snapshot())

        ENGINE.undo_last(self.root)
        self.assertEqual(original_files, self.file_snapshot())
        self.assertEqual(original_directories, self.directory_snapshot())
        self.assertTrue(original.exists())
        self.assertIsNone(ENGINE.undo_last(self.root))

    def test_partial_apply_failure_rolls_back_completed_moves(self):
        first = self.make("Meta/Brazil/Alpha/Stills/Alpha_BRPT_Meta_Still.jpg", b"a")
        second = self.make("Meta/Brazil/Beta/Stills/Beta_BRPT_Meta_Still.jpg", b"b")
        original_files = self.file_snapshot()
        original_directories = self.directory_snapshot()
        _, moves, unresolved, summary = self.plan()
        real_move = shutil.move
        forward_calls = {"count": 0}

        def fail_second_forward(source, destination):
            source_path = Path(source)
            if source_path in {first, second}:
                forward_calls["count"] += 1
                if forward_calls["count"] == 2:
                    raise OSError("synthetic move failure")
            return real_move(source, destination)

        with mock.patch.object(ENGINE.shutil, "move", side_effect=fail_second_forward):
            with self.assertRaises(ENGINE.OrganizationError):
                ENGINE.apply_plan(self.root, moves, unresolved, summary["systemJunk"])

        self.assertEqual(original_files, self.file_snapshot())
        self.assertEqual(original_directories, self.directory_snapshot())
        self.assertFalse((self.root / ".launch-organizer/undo-last.json").exists())


if __name__ == "__main__":
    unittest.main()
