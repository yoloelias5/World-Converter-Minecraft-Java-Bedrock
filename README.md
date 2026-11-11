# WorldBridge — Java to Bedrock

A GitHub Pages frontend and a separate Python API that converts Minecraft Java worlds to Bedrock `.mcworld` files using the [Bridger CLI](https://github.com/MEMOxiiii/bridger).

## Project layout

- `index.html`, `style.css`, `app.js`: static website.
- `config.js`: backend API URL.
- `backend/`: FastAPI service and Docker image.
- `.github/workflows/pages.yml`: automatic GitHub Pages deployment.

## Website deployment

1. Open **Settings → Pages** in this repository.
2. Set the build and deployment source to **GitHub Actions**.
3. Pushes to `main` deploy the website automatically.
4. The website address will be `https://yoloelias5.github.io/World-Converter-Minecraft-Java-Bedrock/`.

## Backend deployment

GitHub Pages cannot run Python or the conversion engine. Deploy the `backend` directory as a Docker service on a host that supports containers and temporary disk space.

The Docker image installs Bridger CLI v1.3.0 and the FastAPI service. The API accepts a ZIP containing a Java world folder (with `level.dat` and `region/`) at `POST /convert/java-to-bedrock`. It returns a `.mcworld` download. Upload limit defaults to 512 MB and conversion timeout to 15 minutes.

Environment variables:
- `BRIDGER_BIN`: CLI executable path (default: `bridger`).
- `MAX_UPLOAD_BYTES`: maximum ZIP upload size.
- `CONVERSION_TIMEOUT`: conversion timeout in seconds.
- `ALLOWED_ORIGINS`: comma-separated website origins. Set this to the GitHub Pages URL for deployment; default is permissive for development.

After deploying the API, edit `config.js` and set:

```js
window.CONVERTER_API_URL = "https://YOUR-BACKEND-HOST";
```

Commit that change to enable the upload button. The API must be publicly reachable over HTTPS for the hosted website to use it.

## Preparing a Java world

1. Make a backup of the original world.
2. Zip the world folder itself (the folder containing `level.dat` and `region/`).
3. Upload the ZIP and wait for the converted `.mcworld`.
4. Open the result with Minecraft Bedrock to import it.

## Conversion notes

Bridger supports Java worlds from Beta 1.3 through 26.3 and writes Bedrock worlds for supported modern versions. Some content has no exact counterpart. The converter requests entity conversion; boats and minecarts are not currently supported. Keep your original world backup.

This project is not affiliated with Mojang or Microsoft. Minecraft is a trademark of Mojang Studios. Bridger is a separate project under the Mozilla Public License 2.0; see its repository for its license and third-party notices.
