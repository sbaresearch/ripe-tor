#!/usr/bin/env Rscript

print("Loading dependencies")
source("00_sources.R")

# Combined Graph
old_asn <- c('AS1299', 'AS2914', 'AS3356', 'AS6939', 'AS24940')

load_destination_paths <- function() {
  parser <- arg_parser("Generate destination-top graphs")
  parser <- add_argument(parser, "--base_path", short = "-b", help = "Path containing values.dat")
  parser <- add_argument(parser, "--output_path", short = "-o", help = "Path to store output files")
  args <- parse_args(parser)

  BASE_PATH <- normalizePath(args$base_path, mustWork = FALSE)
  OUTPUT_PATH <- normalizePath(args$output_path, mustWork = FALSE)

  print(sprintf('Using base path %s', BASE_PATH))
  print(sprintf('Using output path %s', OUTPUT_PATH))

  if (!dir.exists(BASE_PATH)) {
    stop('Given base path ', BASE_PATH, ' does not exist!')
  }

  if (!dir.exists(OUTPUT_PATH)) {
    print(sprintf('Creating output directory %s', OUTPUT_PATH))
    dir.create(OUTPUT_PATH, recursive = TRUE)
  }

  config <- data.frame(
    base = BASE_PATH,
    output = OUTPUT_PATH
  )
  return(config)
}

load_paper_file <- function(base_path, file_name) {
  file_to_load <- paste0(base_path, file_name)
  file_data <- read.table(file_to_load)

  column_names <- c('PEntry', 'PExit', 'PCombined', 'AS', 'ASName', 'FileName')
  colnames(file_data) <- column_names

  return(file_data)
}

load_file <- function(file_name) {
  file_data <- read.table(file_name)

  column_names <- c('PEntry', 'PExit', 'PCombined', 'AS', 'ASName', 'FileName')
  colnames(file_data) <- column_names
  file_data <- file_data %>%
    mutate(country = substr(basename(FileName), 1, 2))

  file_data <- data.frame(file_data)
  file_data$country <- factor(file_data$country, levels = c("DE", "US", "RU"))

  return(file_data)
}

plot_combined <- function(as_data) {
  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Guard Probability", y_label = "Exit Probability")

  alt_name <- as_data %>%
    group_by(AS) %>%
    summarize(n = n()) %>%
    mutate(alt_name = paste0(AS, " (n=", n, ")"))
  file_data <- join(as_data, alt_name, by = "AS")

  file_data <- file_data %>%
    mutate(country = substr(basename(FileName), 1, 2)) %>%
    mutate(as_group = ifelse(AS %in% old_asn, alt_name, "Other"))

  plot <- file_data %>% ggplot() +
    geom_point(aes(color = as_group, x = PEntry, y = PExit), size = 3) +
    geom_function(linetype = 2, fun = function(x) 0.8 / x) +
    geom_function(linetype = 2, fun = function(x) 0.6 / x) +
    geom_function(linetype = 2, fun = function(x) 0.4 / x) +
    geom_function(linetype = 2, fun = function(x) 0.2 / x) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1)) +
    guides(colour = guide_legend(ncol = 3, nrow = 2, byrow = TRUE)) +
    ylim(0, 1) +
    xlim(0, 1) +
    eris_labs +
    eris_theme +
    eris_grid
  return(plot)
}

plot_combined_country <- function(as_data, country_filter) {
  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Guard Probability", y_label = "Exit Probability")

  file_data <- as_data
    filter(country_filter == country)

  alt_name <- file_data %>%
    group_by(AS) %>%
    summarize(n = n()) %>%
    mutate(alt_name = paste0(AS, " (n=", n, ")"))
  file_data <- join(file_data, alt_name, by = "AS")

  file_data <- file_data %>%
    mutate(as_group = ifelse(AS %in% old_asn, alt_name, "Other"))

  plot <- file_data %>%
    ggplot() +
    geom_point(aes(color = as_group, x = PEntry, y = PExit), size = 3) +
    geom_function(linetype = 2, fun = function(x) 0.8 / x) +
    geom_function(linetype = 2, fun = function(x) 0.6 / x) +
    geom_function(linetype = 2, fun = function(x) 0.4 / x) +
    geom_function(linetype = 2, fun = function(x) 0.2 / x) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1)) +
    guides(colour = guide_legend(ncol = 3, nrow = 2, byrow = TRUE)) +
    ylim(0, 1) +
    xlim(0, 1) +
    eris_labs +
    eris_theme +
    eris_grid
  return(plot)
}

plot_combined_shifted <- function(as_data, title = "") {
  x_label <- paste0("Guard Probability - ", title)

  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Guard Probability", y_label = "Exit Probability")

  alt_name <- as_data %>%
    group_by(AS) %>%
    summarize(n = n()) %>%
    mutate(alt_name = paste0(AS, " (n=", n, ")"))
  file_data <- join(as_data, alt_name, by = "AS")

  file_data <- file_data %>%
    mutate(as_group = ifelse(AS %in% old_asn, alt_name, "Other"))

  plot <- file_data %>% ggplot() +
    facet_wrap(~country, nrow = 1) +
    geom_point(aes(color = as_group, x = PEntry, y = PExit), size = 3) +
    geom_function(linetype = 2, fun = function(x) 0.8 / x) +
    geom_function(linetype = 2, fun = function(x) 0.6 / x) +
    geom_function(linetype = 2, fun = function(x) 0.4 / x) +
    geom_function(linetype = 2, fun = function(x) 0.2 / x) +
    scale_x_continuous(labels = percent, limits=c(0,1)) +
    scale_y_continuous(labels = percent, limits=c(0,1)) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1)) +
    guides(colour = guide_legend(nrow = 1, byrow = TRUE)) +
    eris_labs +
    eris_theme +
    eris_grid
  return(plot)
}

generate_combined_graphs_from_paths <- function(config) {
  input_file <- paste0(config$base, "/values.dat")
  as_data <- load_file(input_file)

  plot <- plot_combined(as_data)
  plot_save_square(config$output, '/combined.pdf', plot)
  plot <- plot_combined_country(as_data, "DE")
  plot_save_square(config$output, '/combined_DE.pdf', plot)
  plot <- plot_combined_country(as_data, "US")
  plot_save_square(config$output, '/combined_US.pdf', plot)
  plot <- plot_combined_country(as_data, "RU")
  plot_save_square(config$output, '/combined_RU.pdf', plot)
}

if (FALSE) {
  # load old data
  scan_2020_ipv4 <- "~/coding/work/room5/2022_ripe_tor_cose/paper-source/tables/combined-us/data_source/"
  as1299 <- load_paper_file(scan_2020_ipv4, "values_as1299.dat")
  as2914 <- load_paper_file(scan_2020_ipv4, "values_as2914.dat")
  as3356 <- load_paper_file(scan_2020_ipv4, "values_as3356.dat")
  as6939 <- load_paper_file(scan_2020_ipv4, "values_as6939.dat")
  as24940 <- load_paper_file(scan_2020_ipv4, "values_as24940.dat")
  asothers <- load_paper_file(scan_2020_ipv4, "values_others.dat") %>% mutate(AS = "Other")

  output_2020 <- "/home/havok/Documents/ripetor/images_2020/combined"
  as_data <- rbind(as1299, as2914, as3356, as6939, as24940, asothers)

  plot <- plot_combined(as_data)
  plot_save_square(output_2020, '/2020_combined.pdf', plot)
  plot <- plot_combined_country(as_data, "DE")
  plot_save_square(output_2020, '/2020_combined_DE.pdf', plot)
  plot <- plot_combined_country(as_data, "US")
  plot_save_square(output_2020, '/2020_combined_US.pdf', plot)

  combined_2020_ipv4 <- load_file("~/Documents/ripetor/run_gabriel/real_2022/combined-old/values.dat")
  dummy_line <- list(2.0, 2.0, 4.0, "AS00", "DUMMY ENTRY", "DUMMY FILE", "RU")
  combined_2020_ipv4 <- rbind(combined_2020_ipv4, dummy_line)
  plot <- plot_combined_shifted(combined_2020_ipv4, " - 2020 IPv4")
  plot_save_variable("/home/havok/Documents/ripetor/images_gabriel/", '2020_v4_combined_shifted.pdf', plot, 4500, 1800)

  combined_2022_ipv4 <- load_file("~/Documents/ripetor/run_gabriel/real_2022/combined-us-v4/values.dat")
  plot <- plot_combined_shifted(combined_2022_ipv4, " - 2022 IPv4")
  plot_save_variable("/home/havok/Documents/ripetor/images_gabriel/", '2022_v4_combined_shifted.pdf', plot, 4500, 1800)

  combined_2022_ipv6 <- load_file("~/Documents/ripetor/run_gabriel/real_2022/combined-us-v6/values.dat")
  plot <- plot_combined_shifted(combined_2022_ipv6, " - 2022 IPv6")
  plot_save_variable("/home/havok/Documents/ripetor/images_gabriel/", '2022_v6_combined_shifted.pdf', plot, 4500, 1800)

}

config <- load_destination_paths()
generate_combined_graphs_from_paths(config)
