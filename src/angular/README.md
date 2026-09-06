# GAA Results Angular app

This folder contains the Angular frontend for GAA Results. It currently provides
the landing page and is ready for results and league-table data to be connected.

Angular 22 requires Node.js 22.22.3 or newer.

## Run locally

```sh
cd src/angular
npm install
npm start
```

Then open `http://localhost:4200`.

From the repository root, the same commands are available through `make`:

```sh
make angular-install
make angular-build
make angular-start
make angular-test
```

`angular-test` uses Angular's test runner in single-run mode. Add component
specifications under `src/app` as the application grows.
