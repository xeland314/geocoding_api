from typing import Optional
from pydantic import BaseModel, Field


class Address(BaseModel):
    """Model to represent a formatted address.

    Attributes:
        formatted_address (str): Complete and valid address.
        postcode (Optional[str]): Postcode associated with the address.
        country (Optional[str]): Country to which the address belongs.
        state (Optional[str]): State or province.
        district (Optional[str]): District or region.
        settlement (Optional[str]): City or settlement.
        suburb (Optional[str]): Suburb or neighborhood.
        street (Optional[str]): Street or avenue.
        house (Optional[str]): House or building number.
    """

    formatted_address: str = Field(
        ..., min_length=0, max_length=256, description="Valid address"
    )
    postcode: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    settlement: Optional[str] = None
    suburb: Optional[str] = None
    street: Optional[str] = None
    house: Optional[str] = None

    def format_address(self, format_string: str = "%h %r, %t, %s, %c") -> str:
        """Formats an address based on the given format string.

        Args:
            format_string (str): Format string with placeholders for address components.

        Returns:
            str: Formatted address based on the provided format string.
        """
        mapping = {
            "%p": self.postcode,
            "%c": self.country,
            "%s": self.state,
            "%d": self.district,
            "%t": self.settlement,
            "%u": self.suburb,
            "%r": self.street,
            "%h": self.house,
        }

        # Replace placeholders with actual values or empty strings
        result = format_string
        for placeholder, value in mapping.items():
            result = result.replace(placeholder, value or "")

        # Remove unnecessary delimiters
        parts = [part.strip() for part in result.split(",") if part.strip()]
        return ", ".join(parts).strip()

    def format_address_robust(self, format_string: str = "%h %r, %t, %s, %c") -> str:
        """Formats an address robustly by removing empty components.

        Args:
            format_string (str): Format string with placeholders for address components.

        Returns:
            str: Formatted address or an empty string if all attributes are None.
        """
        formatted = self.format_address(format_string)
        if not any(
            [
                self.postcode,
                self.country,
                self.state,
                self.district,
                self.settlement,
                self.suburb,
                self.street,
                self.house,
            ]
        ):
            return ""
        return formatted

    def __str__(self) -> str:
        """Returns a string representation of the Address object."""
        self.formatted_address = self.format_address_robust()
        return self.formatted_address
