import unittest

from core_common.exceptions import NotFoundError, ServiceCallError
from core_common.models import ErrorEnvelope, GridParams, PagedResponse, ResponseEnvelope


class CoreModelsTests(unittest.TestCase):
    def test_response_envelope_defaults_to_success(self) -> None:
        envelope = ResponseEnvelope(data={"id": "123"}, message="created")

        self.assertTrue(envelope.success)
        self.assertEqual(envelope.data, {"id": "123"})
        self.assertEqual(envelope.message, "created")
        self.assertEqual(envelope.meta, {})

    def test_error_envelope_from_exception(self) -> None:
        error = NotFoundError("user not found")
        envelope = ErrorEnvelope.from_exception(error, correlation_id="cid-1")

        self.assertFalse(envelope.success)
        self.assertEqual(envelope.error["code"], "not_found")
        self.assertEqual(envelope.error["message"], "user not found")
        self.assertEqual(envelope.error["correlation_id"], "cid-1")

    def test_grid_params_clamps_size_and_normalizes_order(self) -> None:
        params = GridParams(page=0, size=250, sort_by="created_at", order="DESC")

        self.assertEqual(params.page, 1)
        self.assertEqual(params.size, 100)
        self.assertEqual(params.order, "desc")
        self.assertEqual(params.offset, 0)

    def test_paged_response_calculates_pages(self) -> None:
        response = PagedResponse(items=[1, 2], total=21, page=2, size=10)

        self.assertEqual(response.pages, 3)
        self.assertEqual(response.items, [1, 2])

    def test_service_exception_preserves_status_and_code(self) -> None:
        error = ServiceCallError("auth-service", "unavailable", status_code=503)

        self.assertEqual(error.service_name, "auth-service")
        self.assertEqual(error.status_code, 503)
        self.assertEqual(error.code, "service_call_error")


if __name__ == "__main__":
    unittest.main()
