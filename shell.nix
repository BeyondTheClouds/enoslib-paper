# https://www.youtube.com/watch?v=TbIHRHy7_JM
# https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md#pythonbuildenv-arguments

let
  pkgs = import <nixpkgs> { };

  # Python 38 with some dependencies
  py-dev = (pkgs.python38.override {
    enableOptimizations = true;
    reproducibleBuild = false;
  }).buildEnv.override {
      extraLibs = with pkgs.python38Packages; [ importmagic epc ];
      ignoreCollisions = true;
  };
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
      py-dev pipenv
      nodePackages.pyright # lsp
      vagrant              # for enoslib
      libpcap              # For fig5.py
      # keep this line if you use bash
      bashInteractive
    ];

    # Set PYTHONPATH to empty to fix `pipenv install`
    PYTHONPATH = "";

    # libpcap lib should be LD_LIBRARY_PATH for fig5.  You can execute
    # it with `pipenv run sudo LD_LIBRARY_PATH=$LD_LIBRARY_PATH python
    # fig5.py`
    LD_LIBRARY_PATH="${pkgs.libpcap}/lib";

    shellHook = ''
    '';
  }
