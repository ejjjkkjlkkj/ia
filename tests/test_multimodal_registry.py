import unittest

from ia_multimodal import CapabilityRegistry, TaskRequest, TaskResult, TaskStatus


class CapabilityRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry()

    def test_unknown_image_handler_is_not_implemented(self):
        result = self.registry.dispatch(
            TaskRequest("image-1", "images", "caption", {"image_ref": "fixture://image"})
        )
        self.assertEqual(result.status, TaskStatus.NOT_IMPLEMENTED)
        self.assertIn("No handler registered", result.message)

    def test_registered_text_handler_dispatches(self):
        def handler(request):
            return TaskResult(
                request_id=request.request_id,
                status=TaskStatus.PASS,
                output={"text": request.payload["text"].upper()},
                evidence=("unit-test-handler",),
            )

        self.registry.register("text", "uppercase", handler)
        result = self.registry.dispatch(
            TaskRequest("text-1", "TEXT", "UpperCase", {"text": "bonjour"})
        )
        self.assertEqual(result.status, TaskStatus.PASS)
        self.assertEqual(result.output, {"text": "BONJOUR"})

    def test_duplicate_registration_is_rejected(self):
        handler = lambda request: TaskResult(request.request_id, TaskStatus.PASS)
        self.registry.register("audio", "transcribe", handler)
        with self.assertRaises(ValueError):
            self.registry.register("AUDIO", "TRANSCRIBE", handler)

    def test_handler_exception_does_not_escape_dispatch(self):
        def handler(request):
            raise RuntimeError("private details must not leak")

        self.registry.register("agents_tools", "plan", handler)
        result = self.registry.dispatch(TaskRequest("agent-1", "agents_tools", "plan"))
        self.assertEqual(result.status, TaskStatus.FAIL)
        self.assertNotIn("private details", result.message)

    def test_invalid_request_fails_closed(self):
        result = self.registry.dispatch(TaskRequest("", "", ""))
        self.assertEqual(result.status, TaskStatus.FAIL)
        self.assertIn("request_id", result.message)
        self.assertIn("modality", result.message)

    def test_handler_must_return_matching_request_id(self):
        self.registry.register(
            "code", "review",
            lambda request: TaskResult("other-id", TaskStatus.PASS)
        )
        result = self.registry.dispatch(TaskRequest("code-1", "code", "review"))
        self.assertEqual(result.status, TaskStatus.FAIL)
        self.assertIn("does not match", result.message)

    def test_non_task_input_fails_closed(self):
        result = self.registry.dispatch({"modality": "text"})
        self.assertEqual(result.status, TaskStatus.FAIL)


if __name__ == "__main__":
    unittest.main()
