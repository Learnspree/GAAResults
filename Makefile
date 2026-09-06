ANGULAR_DIR := src/angular
NPM := npm

.PHONY: angular-install angular-build angular-start angular-test angular

angular-install:
	$(NPM) --prefix $(ANGULAR_DIR) install

angular-build:
	$(NPM) --prefix $(ANGULAR_DIR) run build

angular-start:
	$(NPM) --prefix $(ANGULAR_DIR) start

angular-test:
	$(NPM) --prefix $(ANGULAR_DIR) test

angular: angular-build
