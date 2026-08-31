"""pixiv authentication, backed by [gppt](https://pypi.org/project/gppt/).

gppt owns the credentials, the browser login and the token cache under
`~/.config/gppt/`; this module only turns the token it hands back into an
authenticated `AppPixivAPI`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import gppt
from pixivpy3 import AppPixivAPI

from . import console

if TYPE_CHECKING:
    from gppt import Token

DEFAULT_PROFILE = "default"
"""gppt profile used when `--profile` is not given."""


@dataclass
class PixivClient:
    """An `AppPixivAPI` kept authenticated by a gppt token."""

    token: Token
    profile: str = DEFAULT_PROFILE
    aapi: AppPixivAPI = field(default_factory=AppPixivAPI)

    def __post_init__(self) -> None:
        """Hand the token to the API client."""
        self._apply_token()

    @property
    def user_id(self) -> int:
        """The id of the logged-in account."""
        return int(self.token.user_id)

    def refresh(self) -> None:
        """Trade the refresh token for a new access token.

        A full download can easily outlive the hour an access token is good
        for, so the downloaders call this rather than restarting the login.

        Raises:
            TokenError: If pixiv rejects the refresh token.
        """
        console.info("Access token expired; refreshing...")
        self.token = gppt.refresh(self.token.refresh_token)
        self._apply_token()

    def ensure_fresh(self) -> None:
        """Refresh the access token if it has lapsed, otherwise do nothing."""
        if self.token.is_expired:
            self.refresh()

    def _apply_token(self) -> None:
        self.aapi.set_auth(self.token.access_token, self.token.refresh_token)
        # `set_auth` does not fill this in, but `aapi.user_id` is what the
        # "my own account" endpoints are called with.
        self.aapi.user_id = self.user_id


def login(
    profile: str = DEFAULT_PROFILE,
    *,
    method: str | None = None,
    headless: bool = True,
    force: bool = False,
) -> PixivClient:
    """Log in to pixiv, reusing the cached token whenever it is still usable.

    Args:
        profile: gppt profile name, as created by `gppt configure`.
        method: `"e2e"` to drive a browser with the profile's stored
            credentials, `"oauth"` to log in yourself and paste the code back.
            None uses whatever the profile is configured for.
        headless: Run the login browser without a visible window. Ignored by
            the `oauth` method, and downgraded by gppt when the profile has no
            credentials to type in.
        force: Ignore the cached token and log in again.

    Returns:
        An authenticated client.

    Raises:
        LoginError: If the login does not yield an authorization code.
        TokenError: If pixiv rejects the authorization code.
    """
    token = gppt.get_token(
        profile,
        method=method,
        headless=headless,
        force=force,
        notify=console.info,
        totp_prompt=_prompt_totp,
    )
    return PixivClient(token, profile, AppPixivAPI())


def _prompt_totp() -> str:
    """Ask for a verification code, for a 2FA account with no stored TOTP secret."""
    console.info("pixiv is asking for a two-factor verification code.")
    return input("Verification code: ").strip()
