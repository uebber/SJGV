# SJGV brand assets

| File | Intended channel |
| --- | --- |
| `sjgv-mark-v1.png` | Primary square mark used in the repository README. |
| `sjgv-icon-512.png` | GitHub profile/organisation avatar, app icon, and high-resolution browser icon source. |
| `favicon.ico` | Browser address-bar favicon (64 × 64). |
| `sjgv-social-preview.png` | GitHub repository social-preview image (1280 × 640). |

GitHub does not read a social-preview image from the repository automatically.
Upload `sjgv-social-preview.png` in **Repository Settings → General → Social
preview**. Set `sjgv-icon-512.png` as the avatar of the GitHub account or
organisation that owns the repository; GitHub repositories do not have a
separate icon setting.

For a future project website, expose the browser icon with:

```html
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/assets/sjgv-icon-512.png">
```
