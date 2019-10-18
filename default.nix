with import <nixpkgs> {};
with import <nixpkgs/nixos> {};

let manylinux1Bin = [
    which gcc binutils stdenv
  ];
  manylinux1File = writeTextDir "_manylinux.py" ''
    print("in _manylinux.py")
    manylinux1_compatible = True
  '';
in mkShell {
  buildInputs = [ python37 pipenv manylinux1Bin libffi openssl ];
  shellHook = ''
    export PYTHONPATH=${manylinux1File.out}:''${PYTHONPATH}
  '';
}
