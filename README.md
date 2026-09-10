# OuterClient v5.10.1

## Custom main title bar

v5.10 added a colored focus border around the normal system window.
That was not the intended design.

v5.10.1 removes that outer border completely and replaces the native
Windows/Linux title bar with a real OuterClient title bar.

Features:
- OuterClient logo in the title bar
- centered `OuterClient 5.10.1` title
- custom minimize button
- custom maximize / restore button
- custom close button
- red close hover
- double-click the title bar to maximize/restore
- drag the title bar to move the window
- manual edge/corner resize on borderless Windows and Linux windows
- no purple outline around the whole application

The custom popup dialogs from v5.10 remain enabled.

## Build

GitHub Actions:
`Build and Release OuterClient 5.10.1`

Expected:
- `OuterClient-v5.10.1-x86_64.AppImage`
- `OuterClient-v5.10.1.exe`
