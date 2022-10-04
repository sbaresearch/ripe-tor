##########################################################
# Loads all used libraries for working with the datasets
# Markus 06.07.2022
##########################################################
LIB_PATH <- "~/.Rlibs/"
.libPaths(c(.libPaths(), LIB_PATH))

shhh <- suppressPackageStartupMessages # It's a library, so shhh!
shhh(library("rlang"))
shhh(library("Rmisc"))
shhh(library("scales"))
shhh(library("magrittr"))
shhh(library("tidyr"))
shhh(library("dplyr"))
shhh(library("ggplot2"))
shhh(library("grid"))
shhh(library("gridExtra"))
shhh(library("stringr"))
shhh(library("ggpolypath"))
shhh(library("argparser"))
print("Loading Libraries DONE")
