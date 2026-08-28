from typing import Any


class AgentCommunication:
    """
    Communication bridge between an external agent and
    the Merchant Agent.

    For now, this contains placeholder implementations.
    Later, these methods will communicate with the actual
    Merchant Agent and return real JSON data.
    """

    def get_products(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Ask the Merchant Agent for products and product details.

        The exact request fields will be decided later.
        """

        print("External agent requested product information:")
        print(request)

        # Temporary placeholder response
        return {
            "success": True,
            "message": "Product request received by Merchant Agent",
            "request": request,
            "products": [],
        }

    def place_order(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Ask the Merchant Agent to place an order.

        The exact request fields will be decided later.
        """

        print("External agent requested an order:")
        print(request)

        # Temporary placeholder response
        return {
            "success": True,
            "message": "Order request received by Merchant Agent",
            "request": request,
            "order": None,
        }