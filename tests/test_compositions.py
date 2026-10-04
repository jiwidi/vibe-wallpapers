"""Focused tests of composition correctness and safe repeated rendering."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from compositions import (ROOT, CompositionError, CompositionService, Options, Placement,
                          TransformedCanvas, compose_record, source_bounds)
from generators.core import Canvas


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ROOT / 'gallery' / 'manifest.json').read_text())
        cls.records = {r['id']: r for r in manifest['wallpapers']}

    def test_validation_rejects_unbounded_requests(self):
        for change in ({'width': 100000}, {'layout': 'unknown'}, {'density': 50}, {'seed': -1}):
            values = dict(id='circuit-forests-03', layout='repeat', width=960, height=540, density=2, seed=0)
            values.update(change)
            with self.assertRaises(CompositionError):
                Options(**values).validate()

    def test_black_field_paste_preserves_existing_art(self):
        c = Canvas(160, 90, ['#002233', '#336677'])
        c.image.paste((130, 20, 0), (0, 0, 160, 90))
        proxy = TransformedCanvas(c, Placement(.8, .4, .1, -.1), (-.5, -.5, .5, .5))
        source = np.zeros((70, 70, 3), np.uint8)
        source[20:50, 20:50, 1] = 200
        proxy.paste_field(source, (-.5, -.5, .5, .5))
        pixels = np.asarray(c.image)
        self.assertTrue(np.all(pixels[:, :, 0] == 130))
        self.assertGreater(int(pixels[:, :, 1].max()), 190)
        self.assertEqual(int(pixels[0, 0, 1]), 20)

    def test_fresh_bounds_need_no_original_image(self):
        record = dict(self.records['circuit-forests-03'])
        record.pop('source_bounds', None)
        record['files'] = []
        with tempfile.TemporaryDirectory() as empty:
            bounds = source_bounds(record, root=Path(empty))
        self.assertGreater(bounds[2] - bounds[0], .5)
        self.assertGreater(bounds[3] - bounds[1], .3)

    def test_vector_composition_is_deterministic_and_fills_frame(self):
        record = self.records['circuit-forests-03']
        a, meta = compose_record(record, 'repeat', 960, 540, density=2, seed=19)
        b, _ = compose_record(record, 'repeat', 960, 540, density=2, seed=19,
                              source_bounds=meta['source_bounds'])
        self.assertEqual(a.tobytes(), b.tobytes())
        mask = np.max(np.asarray(a), axis=2) > 8
        self.assertTrue(mask[:, :120].any())
        self.assertTrue(mask[:, -120:].any())
        self.assertTrue(mask[:90].any())
        self.assertTrue(mask[-90:].any())

    def test_native_clifford_and_cache_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            service = CompositionService(cache_dir=directory)
            options = Options('clifford-veils-01', 'fill', 960, 540, 2, 0)
            first = service.render(options)
            second = service.render(options)
            self.assertFalse(first.cache_hit)
            self.assertTrue(second.cache_hit)
            self.assertEqual(first.path, second.path)
            with Image.open(first.path) as image:
                self.assertEqual(image.size, (960, 540))
                self.assertIn('interacting physical simulation', image.info['Description'])
                self.assertIn('source_bounds', json.loads(image.info['Composition']))
                self.assertGreater(np.count_nonzero(np.asarray(image)), 10000)

    def test_focus_camera_preserves_neutral_bounds(self):
        record = self.records['circuit-forests-03']
        neutral = source_bounds(record)
        focus = (-.3, -.2, .2, .2)
        with patch('compositions._display_bounds', return_value=focus):
            _, meta = compose_record(record, 'fill', 960, 540, source_bounds=neutral)
        self.assertEqual(meta['source_bounds'], list(neutral))
        self.assertEqual(meta['focus_bounds'], list(focus))

    def test_live_service_keeps_loaded_renderer_cache_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            service = CompositionService(cache_dir=directory)
            options = Options('circuit-forests-03', 'repeat', 960, 540, 2, 0)
            first = service.render(options)
            with patch('compositions.renderer_fingerprint', return_value='new-files-not-yet-loaded'):
                second = service.render(options)
            self.assertTrue(second.cache_hit)
            self.assertEqual(first.path, second.path)
            with Image.open(first.path) as image:
                saved = json.loads(image.info['Composition'])
                self.assertEqual(saved['renderer_fingerprint'], service.fingerprint)


if __name__ == '__main__':
    unittest.main()
