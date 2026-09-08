ANGULAR_DIR := src/angular
ANGULAR_DIST := $(ANGULAR_DIR)/dist/gaa-results/browser
NPM := npm
FRONTEND_BUCKET ?=
CLOUDFRONT_DISTRIBUTION_ID ?=

.PHONY: angular-install angular-build angular-start angular-test angular angular-deploy cloudfront-invalidate

angular-install:
	$(NPM) --prefix $(ANGULAR_DIR) install

angular-build:
	$(NPM) --prefix $(ANGULAR_DIR) run build

angular-start:
	$(NPM) --prefix $(ANGULAR_DIR) start

angular-test:
	$(NPM) --prefix $(ANGULAR_DIR) test

angular: angular-build

angular-deploy:
	@test -n "$(FRONTEND_BUCKET)" || (echo "FRONTEND_BUCKET is required" && exit 1)
	@test -n "$(CLOUDFRONT_DISTRIBUTION_ID)" || (echo "CLOUDFRONT_DISTRIBUTION_ID is required" && exit 1)
	$(MAKE) angular-build
	aws s3 sync $(ANGULAR_DIST) s3://$(FRONTEND_BUCKET) --delete --exclude index.html --cache-control "public,max-age=31536000,immutable"
	aws s3 cp $(ANGULAR_DIST)/index.html s3://$(FRONTEND_BUCKET)/index.html --cache-control "no-cache,no-store,must-revalidate" --content-type "text/html"
	aws cloudfront create-invalidation --distribution-id "$(CLOUDFRONT_DISTRIBUTION_ID)" --paths "/index.html"

cloudfront-invalidate:
	@test -n "$(CLOUDFRONT_DISTRIBUTION_ID)" || (echo "CLOUDFRONT_DISTRIBUTION_ID is required" && exit 1)
	aws cloudfront create-invalidation --distribution-id "$(CLOUDFRONT_DISTRIBUTION_ID)" --paths "/index.html"
