import importlib
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock


def _install_compute_worker_stubs():
    if "docker" not in sys.modules:
        docker_mod = types.ModuleType("docker")
        docker_mod.APIClient = lambda *args, **kwargs: object()
        docker_mod.errors = types.SimpleNamespace(
            APIError=Exception, NotFound=Exception
        )
        sys.modules["docker"] = docker_mod

    if "rich" not in sys.modules:
        rich_mod = types.ModuleType("rich")
        sys.modules["rich"] = rich_mod
        progress_mod = types.ModuleType("rich.progress")

        class _Progress:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def add_task(self, *args, **kwargs):
                return 1

            def update(self, *args, **kwargs):
                return None

        progress_mod.Progress = _Progress
        pretty_mod = types.ModuleType("rich.pretty")
        pretty_mod.pprint = lambda *args, **kwargs: None
        sys.modules["rich.progress"] = progress_mod
        sys.modules["rich.pretty"] = pretty_mod

    if "requests" not in sys.modules:
        requests_mod = types.ModuleType("requests")

        class _HTTPAdapter:
            def __init__(self, *args, **kwargs):
                pass

        class _Session:
            def mount(self, *args, **kwargs):
                return None

        requests_mod.Session = _Session
        requests_mod.adapters = types.SimpleNamespace(HTTPAdapter=_HTTPAdapter)
        requests_mod.RequestException = Exception
        requests_mod.exceptions = types.SimpleNamespace(ReadTimeout=Exception)
        sys.modules["requests"] = requests_mod

    if "websockets" not in sys.modules:
        websockets_mod = types.ModuleType("websockets")
        websockets_mod.connect = lambda *args, **kwargs: None
        websockets_mod.WebSocketException = Exception
        websockets_mod.ConnectionClosedError = Exception
        sys.modules["websockets"] = websockets_mod

    if "yaml" not in sys.modules:
        yaml_mod = types.ModuleType("yaml")
        yaml_mod.FullLoader = object
        yaml_mod.Loader = object
        yaml_mod.load = lambda *args, **kwargs: {}
        yaml_mod.dump = lambda *args, **kwargs: ""
        sys.modules["yaml"] = yaml_mod

    if "billiard" not in sys.modules:
        billiard_mod = types.ModuleType("billiard")
        billiard_ex_mod = types.ModuleType("billiard.exceptions")

        class _SoftTimeLimitExceeded(Exception):
            pass

        billiard_ex_mod.SoftTimeLimitExceeded = _SoftTimeLimitExceeded
        sys.modules["billiard"] = billiard_mod
        sys.modules["billiard.exceptions"] = billiard_ex_mod

    if "celery" not in sys.modules:
        celery_mod = types.ModuleType("celery")

        class _Celery:
            def __init__(self, *args, **kwargs):
                self.conf = types.SimpleNamespace()

            def config_from_object(self, *args, **kwargs):
                return None

        def _shared_task(*args, **kwargs):
            def _decorator(func):
                return func

            return _decorator

        celery_mod.Celery = _Celery
        celery_mod.shared_task = _shared_task
        celery_mod.utils = types.SimpleNamespace(
            nodenames=types.SimpleNamespace(gethostname=lambda: "test-host")
        )
        celery_mod.signals = types.SimpleNamespace(
            setup_logging=types.SimpleNamespace(connect=lambda func: func)
        )
        sys.modules["celery"] = celery_mod

    if "kombu" not in sys.modules:
        kombu_mod = types.ModuleType("kombu")
        kombu_mod.Queue = lambda *args, **kwargs: ("queue", args, kwargs)
        kombu_mod.Exchange = lambda *args, **kwargs: ("exchange", args, kwargs)
        sys.modules["kombu"] = kombu_mod

    if "urllib3" not in sys.modules:
        urllib3_mod = types.ModuleType("urllib3")

        class _Retry:
            def __init__(self, *args, **kwargs):
                pass

        urllib3_mod.Retry = _Retry
        sys.modules["urllib3"] = urllib3_mod

    if "logs_loguru" not in sys.modules:
        logs_loguru_mod = types.ModuleType("logs_loguru")
        logs_loguru_mod.configure_logging = lambda *args, **kwargs: None
        logs_loguru_mod.colorize_run_args = lambda text: text
        sys.modules["logs_loguru"] = logs_loguru_mod


_install_compute_worker_stubs()
cw = importlib.import_module("compute_worker.compute_worker")


class ComputeWorkerNoIngestionTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="cw-no-ingestion-")
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

    def _make_run(self, is_scoring=False, disable_ingestion=True):
        run = cw.Run.__new__(cw.Run)
        run.is_scoring = is_scoring
        run.disable_ingestion = disable_ingestion
        run.submission_id = 17
        run.root_dir = self.tmpdir
        run.bundle_dir = os.path.join(self.tmpdir, "bundles")
        run.input_dir = os.path.join(self.tmpdir, "input")
        run.output_dir = os.path.join(self.tmpdir, "output")
        run.program_data = "program-url"
        run.ingestion_program_data = "ingestion-url"
        run.input_data = "input-url"
        run.reference_data = "ref-url"
        run.prediction_result = "prediction-url"
        run.container_image = "image:latest"
        run.execution_time_limit = 60
        run.program_exit_code = None
        run.ingestion_program_exit_code = None
        run.program_elapsed_time = None
        run.ingestion_elapsed_time = None
        run.completed_program_counter = 0
        run.watch = True
        run.requests_session = mock.Mock()
        return run

    def test_download_bundle_uses_aria2c_when_available(self):
        run = self._make_run()
        bundle_file = os.path.join(self.tmpdir, "bundle.zip")

        with (
            mock.patch.object(cw, "USE_ARIA2C", True),
            mock.patch.object(cw.shutil, "which", return_value="/usr/bin/aria2c"),
            mock.patch.object(cw.subprocess, "run", return_value=mock.Mock(returncode=0)) as run_mock,
        ):
            run._download_bundle("https://example.com/test.zip", bundle_file)

        run.requests_session.get.assert_not_called()
        cmd = run_mock.call_args.args[0]
        self.assertIn("/usr/bin/aria2c", cmd)
        self.assertIn("--split=8", cmd)
        self.assertIn("https://example.com/test.zip", cmd)

    def test_download_bundle_falls_back_to_requests_when_aria2c_missing(self):
        run = self._make_run()
        bundle_file = os.path.join(self.tmpdir, "bundle.zip")
        response = mock.Mock()
        response.iter_content.return_value = [b"abc", b"def"]
        run.requests_session.get.return_value = response

        with (
            mock.patch.object(cw, "USE_ARIA2C", True),
            mock.patch.object(cw.shutil, "which", return_value=None),
        ):
            run._download_bundle("https://example.com/test.zip", bundle_file)

        run.requests_session.get.assert_called_once_with(
            "https://example.com/test.zip", stream=True, timeout=150
        )
        with open(bundle_file, "rb") as fh:
            self.assertEqual(fh.read(), b"abcdef")

    def test_download_bundle_falls_back_to_requests_when_aria2c_fails(self):
        run = self._make_run()
        bundle_file = os.path.join(self.tmpdir, "bundle.zip")
        response = mock.Mock()
        response.iter_content.return_value = [b"fallback"]
        run.requests_session.get.return_value = response

        with (
            mock.patch.object(cw, "USE_ARIA2C", True),
            mock.patch.object(cw.shutil, "which", return_value="/usr/bin/aria2c"),
            mock.patch.object(
                cw.subprocess,
                "run",
                return_value=mock.Mock(returncode=1, stderr="boom"),
            ),
        ):
            run._download_bundle("https://example.com/test.zip", bundle_file)

        run.requests_session.get.assert_called_once()
        with open(bundle_file, "rb") as fh:
            self.assertEqual(fh.read(), b"fallback")

    def test_cache_and_restore_submission_bundle(self):
        run = self._make_run()
        program_dir = os.path.join(self.tmpdir, "program")
        os.makedirs(program_dir, exist_ok=True)
        sample_file = os.path.join(program_dir, "submission.txt")
        with open(sample_file, "w", encoding="utf-8") as fh:
            fh.write("cached-submission")

        original_cache_dir = cw.CACHE_DIR
        cw.CACHE_DIR = os.path.join(self.tmpdir, "cache")
        os.makedirs(cw.CACHE_DIR, exist_ok=True)
        try:
            run._cache_submission_for_scoring()
            shutil.rmtree(program_dir)
            run._restore_cached_submission_for_scoring()
        finally:
            cw.CACHE_DIR = original_cache_dir

        restored_file = os.path.join(self.tmpdir, "input", "res", "submission.txt")
        self.assertTrue(os.path.exists(restored_file))
        with open(restored_file, "r", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "cached-submission")

    def test_prepare_prediction_skips_ingestion_and_caches_submission(self):
        run = self._make_run(is_scoring=False, disable_ingestion=True)
        original_cache_dir = cw.CACHE_DIR
        cw.CACHE_DIR = os.path.join(self.tmpdir, "cache")
        os.makedirs(cw.CACHE_DIR, exist_ok=True)
        bundle_calls = []
        update_calls = []

        def _fake_get_bundle(url, path, cache):
            bundle_calls.append((url, path, cache))
            bundle_file = os.path.join(self.tmpdir, f"{path.replace('/', '_')}.zip")
            with open(bundle_file, "wb") as fh:
                fh.write(b"bundle")
            if path == "program":
                os.makedirs(os.path.join(self.tmpdir, "program"), exist_ok=True)
                with open(
                    os.path.join(self.tmpdir, "program", "main.py"),
                    "w",
                    encoding="utf-8",
                ) as fh:
                    fh.write("print('ok')")
            return bundle_file

        run._update_status = mock.Mock()
        run._prep_cache_dir = mock.Mock()
        run._get_bundle = mock.Mock(side_effect=_fake_get_bundle)
        run._update_submission = mock.Mock(side_effect=update_calls.append)
        run._get_container_image = mock.Mock()
        run._cache_submission_for_scoring = mock.Mock()

        try:
            run.prepare()
        finally:
            cw.CACHE_DIR = original_cache_dir

        fetched_paths = [path for _, path, _ in bundle_calls]
        self.assertEqual(fetched_paths, ["program", "input_data", "input/ref"])
        run._cache_submission_for_scoring.assert_called_once()
        run._get_container_image.assert_not_called()
        self.assertTrue(any(call.get("md5") for call in update_calls))

    def test_start_prediction_short_circuits_in_no_ingestion_mode(self):
        run = self._make_run(is_scoring=False, disable_ingestion=True)
        run._update_status = mock.Mock()

        run.start()

        self.assertEqual(run.program_exit_code, 0)
        self.assertEqual(run.ingestion_program_exit_code, 0)
        run._update_status.assert_called_once_with(cw.STATUS_SCORING)


if __name__ == "__main__":
    unittest.main()
