#!/usr/bin/env Rscript

LIB_PATH <- "~/.Rlibs/"
dir.create(LIB_PATH, recursive = TRUE)

r <- getOption("repos")
r["CRAN"] <- "http://cran.us.r-project.org"
options(repos = r)

install.packages("rlang", LIB_PATH)
install.packages("ggpolypath", LIB_PATH)
install.packages("ggplot2", LIB_PATH)
install.packages("dplyr", LIB_PATH)
install.packages("Rmisc", LIB_PATH)
install.packages("gridExtra", LIB_PATH)
install.packages("tidyr", LIB_PATH)
install.packages('stringi',LIB_PATH)
install.packages("stringr", LIB_PATH)
install.packages("shiny", LIB_PATH)
install.packages("remotes", LIB_PATH)
install.packages("argparser", LIB_PATH)
