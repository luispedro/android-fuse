#!/usr/bin/env nix-shell

with import <nixpkgs> {};

let
    envname = "android_fuse";
    python = python27Full;
    pyp = pkgs.python27Packages;
in

buildPythonPackage { 
  name = "${envname}-env";
  buildInputs = [
    python
    zsh
  ];
  propagatedBuildInputs = [
    androidsdk_4_4
  ];
  pythonPath = with pyp; [
    fusepy
  ];
  src = null;
  # When used as `nix-shell --pure`
  shellHook = ''
  export NIX_ENV="[${envname}] "
  exec zsh
  '';
  # used when building environments
  extraCmds = ''
  export NIX_ENV="[${envname}] "
  '';
}

