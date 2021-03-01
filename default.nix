with import <nixpkgs> {};

let packageOverrides = self: super: {
    # Override python-language-server at top level to make it effective
    # also for isort and mypy
    python-language-server = super.python-language-server.override {
      # Only make few features available
      # https://github.com/NixOS/nixpkgs/blob/e5a015bd85f6d1578702aaa7e710b028775c76aa/pkgs/development/python-modules/python-language-server/default.nix
      providers = [
        "pycodestyle"  # Style linting (Ex-pep8)
        "pyflakes"     # Error linting (no style)
      ];
    };
  };
  py-dev = (python38.override {inherit packageOverrides;}).withPackages (py-pkg: [
                py-pkg.python-language-server
                py-pkg.pyls-isort
                py-pkg.pyls-mypy
            ]);
  # Put libpcap in LD_LIBRARY_PATH in an `.env` file.  The `.env` file
  # is read by pipenv, so environment variable in this file will be
  # available in a `pipenv shell`.
  pipenv-env = writeText ".env" ''
    LD_LIBRARY_PATH=${libpcap}/lib
  '';
in mkShell {
  buildInputs = [ py-dev pipenv libffi openssl vagrant
                  libpcap
                ];
  shellHook = ''
    # Set SOURCE_DATE_EPOCH so that we can use python wheels
    SOURCE_DATE_EPOCH=$(date +%s)

    # Set PYTHONPATH to empty to fix `pipenv install`
    PYTHONPATH=

    # Link the `.env` file
    ln -fs ${pipenv-env} .env
  '';
}