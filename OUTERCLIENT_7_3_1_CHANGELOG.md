# OuterClient 7.3.1

Hotfix release for two regressions reported after 7.3.0:

- clear stale `Uruchamianie Minecrafta...` footer/progress after Minecraft starts, exits or fails, with generation guards so old launch callbacks cannot overwrite a newer session;
- restore Microsoft account-card actions `Zmień skina` and `Zmień nick` and reuse the already-loaded Minecraft skin head from the sidebar when available.

The 7.3.1 workflow also runs the existing 7.3.0 core tests plus new footer regression tests before building Windows EXE and Linux AppImage artifacts.
