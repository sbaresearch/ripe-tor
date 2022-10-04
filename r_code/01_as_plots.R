#!/usr/bin/env Rscript

print("Loading dependencies")
source("00_sources.R")

LINE_THICKNESS <- 1

load_as_paths <- function() {
  parser <- arg_parser("Generate basic AS graphs")
  parser <- add_argument(parser, "--base_path", short = "-b", help = "Path containing both gnuplot_2020 and gnuplot_2022")
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

load_asn_data <- function(base_path, as_type, probe_type, exit = FALSE, ipv4 = FALSE) {
  base <- "guard"
  proto <- "ipv6"

  if (exit) {
    base <- "exit"
  }

  if (ipv4) {
    proto <- "ipv4"
  }

  as_file <- paste0(base_path, "/", base, "_", proto, "_as.dat")
  probes_file <- paste0(base_path, "/", base, "_", proto, "_probes_as.dat")

  data_as <- read.table(as_file, header = FALSE) %>%
    mutate(type = as_type)

  data_probes <- read.table(probes_file, header = FALSE) %>%
    mutate(type = probe_type)

  column_names <- c("index", "perc", "num", "type")
  colnames(data_as) <- column_names
  colnames(data_probes) <- column_names

  rbind(data_as, data_probes)
}

plot_data <- function(data, xlim, x_label, y_label, bw_theme = FALSE) {

  eris_theme <- get_eris_theme(bw_theme = bw_theme)
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = x_label, y_label = y_label)

  data %>%
    ggplot() +
    geom_line(aes(x = index, y = perc, color = type), size = LINE_THICKNESS) +
    coord_cartesian(xlim = c(0, xlim)) +
    scale_color_manual(values=ERIS_COLORS_COL) +
    eris_labs +
    eris_theme +
    eris_grid
}

plot_path_wrapper <- function(base_path, x_label, exit = FALSE, ipv4 = FALSE) {
  as_type <- "All AS"
  probe_type <- "AS with RIPE Atlas Probe"

  data <- load_asn_data(base_path, as_type, probe_type, exit, ipv4)
  plot_data_wrapper(data, x_label, exit)
}

plot_data_wrapper <- function(data, x_label, exit = FALSE, bw_theme = FALSE) {
  xlim <- 100
  plot_label <- "Guard Probability"

  if (exit) {
    xlim <- 100
    plot_label <- "Exit Probability"
  }

  plot_data(data, xlim, x_label, plot_label, bw_theme)
}

plot_single_graph <- function(data, y_label, x_lim, bw_theme = FALSE) {

  eris_theme <- get_eris_theme(bw_theme = bw_theme)
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Number of AS", y_label = y_label)

  data %>%
    ggplot() +
    geom_line(aes(x = index, y = perc, color = data_line, linetype = type), size = LINE_THICKNESS) +
    coord_cartesian(xlim = c(0, x_lim)) +
    scale_color_manual(values=ERIS_COLORS_COL) +
    eris_labs +
    eris_theme +
    eris_grid
}

generate_as_graphs_from_paths <- function(config) {
  BASE_PATH <- config$base
  OUTPUT_PATH <- config$output

  path_2020 <- paste0(BASE_PATH, "/gnuplot_2020/")
  path_2022 <- paste0(BASE_PATH, "/gnuplot_2022/")

  as_type <- "All AS"
  probe_type <- "AS with RIPE Atlas Probe"

  data_guard_ipv4_2020 <- load_asn_data(path_2020, as_type, probe_type, ipv4 = TRUE)
  data_guard_ipv4_2022 <- load_asn_data(path_2022, as_type, probe_type, ipv4 = TRUE)
  data_guard_ipv6_2022 <- load_asn_data(path_2022, as_type, probe_type, ipv4 = FALSE)

  data_exit_ipv4_2020 <- load_asn_data(path_2020, as_type, probe_type, exit = TRUE, ipv4 = TRUE)
  data_exit_ipv4_2022 <- load_asn_data(path_2022, as_type, probe_type, exit = TRUE, ipv4 = TRUE)
  data_exit_ipv6_2022 <- load_asn_data(path_2022, as_type, probe_type, exit = TRUE, ipv4 = FALSE)

  # normalize ipv6 data
  guard_modifier <- 1 / max(data_guard_ipv6_2022$perc)
  exit_modifier <- 1 / max(data_exit_ipv6_2022$perc)

  data_guard_ipv6_2022 <- data_guard_ipv6_2022 %>% mutate(perc = perc * guard_modifier)
  data_exit_ipv6_2022 <- data_exit_ipv6_2022 %>% mutate(perc = perc * exit_modifier)

  sprintf("Creating plots for 2020")
  plot <- plot_data_wrapper(data_guard_ipv4_2020, "Number of AS in IPv4 (2020)")
  plot_save(OUTPUT_PATH, "guard_ipv4_2020.pdf", plot)
  plot <- plot_data_wrapper(data_exit_ipv4_2020, "Number of AS in IPv4 (2020)", exit = TRUE)
  plot_save(OUTPUT_PATH, "exit_ipv4_2020.pdf", plot)

  sprintf("Creating plots for 2022 IPV4")
  plot <- plot_data_wrapper(data_guard_ipv4_2022, "Number of AS in IPv4 (2022)")
  plot_save(OUTPUT_PATH, "guard_ipv4_2022.pdf", plot)
  plot <- plot_data_wrapper(data_exit_ipv4_2022, "Number of AS in IPv4 (2022)", exit = TRUE)
  plot_save(OUTPUT_PATH, "exit_ipv4_2022.pdf", plot)

  sprintf("Creating plots for 2022 IPv6")
  plot <- plot_data_wrapper(data_guard_ipv6_2022, "Number of AS in IPv6 (2022)")
  plot_save(OUTPUT_PATH, "guard_ipv6_2022.pdf", plot)
  plot <- plot_data_wrapper(data_exit_ipv6_2022, "Number of AS in IPv6 (2022)", exit = TRUE)
  plot_save(OUTPUT_PATH, "exit_ipv6_2022.pdf", plot)

  exit_v4_2020 <- data_exit_ipv4_2020 %>% mutate(data_line = "IPv4 2020")
  exit_v4_2022 <- data_exit_ipv4_2022 %>% mutate(data_line = "IPv4 2022")
  exit_v6_2022 <- data_exit_ipv6_2022 %>% mutate(data_line = "IPv6 2022")
  exit_data <- rbind(exit_v4_2020, exit_v4_2022, exit_v6_2022) %>% mutate(direction = "exit")

  guard_v4_2020 <- data_guard_ipv4_2020 %>% mutate(data_line = "IPv4 2020")
  guard_v4_2022 <- data_guard_ipv4_2022 %>% mutate(data_line = "IPv4 2022")
  guard_v6_2022 <- data_guard_ipv6_2022 %>% mutate(data_line = "IPv6 2022")
  guard_data <- rbind(guard_v4_2020, guard_v4_2022, guard_v6_2022) %>% mutate(direction = "guard")

  combined_data <- rbind(exit_data, guard_data)

  sprintf("Creating combined plots")
  plot <- plot_single_graph(guard_data, "Guard Probablity", 100)
  plot_save(OUTPUT_PATH, "guard_all.pdf", plot)

  plot <- plot_single_graph(exit_data, "Exit Probablity", 100)
  plot_save(OUTPUT_PATH, "exit_all.pdf", plot)

  # do white graphs
  sprintf("Creating combined plots... in WHITE")
  plot <- plot_single_graph(exit_data, "Exit Probablity", 100, bw_theme = TRUE)
  plot_save(OUTPUT_PATH, "exit_all_white.pdf", plot)

  plot <- plot_single_graph(guard_data, "Guard Probablity", 100, bw_theme = TRUE)
  plot_save(OUTPUT_PATH, "guard_all_white.pdf", plot)

  # do side by side graphs to only have one common legend
  plot <- plot_shifted_graph(combined_data, "Probability", 100)
  plot_save_variable(OUTPUT_PATH, "combined.pdf", plot, 4000, ERIS_DEFAULT_HEIGHT)

  plot <- plot_shifted_graph(combined_data, "Probability", 100, below = TRUE)
  plot_save_variable(OUTPUT_PATH, "combined_below.pdf", plot, ERIS_DEFAULT_WIDTH, 2500)
}

plot_shifted_graph <- function(data, y_label, x_lim, bw_theme = FALSE, below = FALSE) {
  eris_theme <- get_eris_theme(bw_theme = bw_theme)
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Number of AS", y_label = y_label)

  nrow <- 1
  strip_position <- "top"
  if (below) {
    nrow <- 2
    strip_position <- "right"
  }

  data %>%
    ggplot() +
    geom_line(aes(x = index, y = perc, color = data_line, linetype = type), size = LINE_THICKNESS) +
    coord_cartesian(xlim = c(0, x_lim)) +
    facet_wrap(~direction, nrow = nrow, strip.position = strip_position) +
    scale_color_manual(values=ERIS_COLORS_COL) +
    eris_labs +
    eris_theme +
    eris_grid
}

if (FALSE) {
  # MANUAL STUFF
  path_2020 <- "~/coding/work/room5/2022_ripe-tor-data/gnuplot_2020/"
  plot_path_wrapper(path_2020, exit = FALSE, ipv4 = TRUE)
  plot_path_wrapper(path_2020, exit = FALSE, ipv4 = FALSE)
  plot_path_wrapper(path_2020, exit = TRUE, ipv4 = TRUE)
  plot_path_wrapper(path_2020, exit = TRUE, ipv4 = FALSE)

  path_2022 <- "~/coding/work/room5/2022_ripe-tor-data/gnuplot_2022/"
  plot_path_wrapper(path_2022, exit = FALSE, ipv4 = TRUE)
  plot_path_wrapper(path_2022, exit = FALSE, ipv4 = FALSE)
  plot_path_wrapper(path_2022, exit = TRUE, ipv4 = TRUE)
  plot_path_wrapper(path_2022, exit = TRUE, ipv4 = FALSE)

  as_type <- "All AS"
  probe_type <- "AS with RIPE Atlas Probe"

  data_guard_ipv4_2020 <- load_asn_data(path_2020, as_type, probe_type, ipv4 = TRUE)
  data_guard_ipv4_2022 <- load_asn_data(path_2022, as_type, probe_type, ipv4 = TRUE)
  data_guard_ipv6_2022 <- load_asn_data(path_2022, as_type, probe_type, ipv4 = FALSE)

  data_exit_ipv4_2020 <- load_asn_data(path_2020, as_type, probe_type, exit = TRUE, ipv4 = TRUE)
  data_exit_ipv4_2022 <- load_asn_data(path_2022, as_type, probe_type, exit = TRUE, ipv4 = TRUE)
  data_exit_ipv6_2022 <- load_asn_data(path_2022, as_type, probe_type, exit = TRUE, ipv4 = FALSE)

  exit_v4_2020 <- data_exit_ipv4_2020 %>% mutate(data_line = "IPv4 2020")
  exit_v4_2022 <- data_exit_ipv4_2022 %>% mutate(data_line = "IPv4 2022")
  exit_v6_2022 <- data_exit_ipv6_2022 %>% mutate(data_line = "IPv6 2022")
  exit_data <- rbind(exit_v4_2020, exit_v4_2022, exit_v6_2022) %>% mutate(direction = "exit")

  guard_v4_2020 <- data_guard_ipv4_2020 %>% mutate(data_line = "IPv4 2020")
  guard_v4_2022 <- data_guard_ipv4_2022 %>% mutate(data_line = "IPv4 2022")
  guard_v6_2022 <- data_guard_ipv6_2022 %>% mutate(data_line = "IPv6 2022")
  guard_data <- rbind(guard_v4_2020, guard_v4_2022, guard_v6_2022) %>% mutate(direction = "guard")

  combined_data <- rbind(exit_data, guard_data)

  plot_single_graph(guard_data, "Guard Probablity", 100)
  plot_single_graph(exit_data, "Exit Probablity", 100)
  plot_shifted_graph(combined_data, "Probability", 100, below = TRUE)

}

config <- load_as_paths()
generate_as_graphs_from_paths(config)