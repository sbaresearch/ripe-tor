#!/usr/bin/env Rscript

print("Loading dependencies")
source("00_sources.R")

#### Destination TOP

DESTINATION_OLD_ORDER <- c('AS6939', 'AS6461', 'AS174', 'AS1299', 'AS1200', 'AS2914', 'AS10578', 'AS3257')

load_destination_paths <- function() {
  parser <- arg_parser("Generate destination-top graphs")
  parser <- add_argument(parser, "--base_path", short = "-b", help = "Path containing destination-top.dat")
  parser <- add_argument(parser, "--output_path", short = "-o", help = "Path to store output file")
  parser <- add_argument(parser, "--output_filename", short = "-f", help = "Name of the output file")
  parser <- add_argument(parser, "--use_tsv", short = "-t", flag=TRUE, help = "Input file is old TSV file")
  parser <- add_argument(parser, "--filter", short = "-z", flag=TRUE, help = "Use Median Filter")
  args <- parse_args(parser)

  BASE_PATH <- normalizePath(args$base_path, mustWork = FALSE)
  OUTPUT_PATH <- normalizePath(args$output_path, mustWork = FALSE)
  OUTPUT_NAME <- args$output_filename
  is_tsv <- args$use_tsv
  use_filter <- args$filter

  print(sprintf('Using base path %s', BASE_PATH))
  print(sprintf('Using output path %s', OUTPUT_PATH))
  print(sprintf('Using file name %s', OUTPUT_NAME))
  print(sprintf('Using TSV reader %s', is_tsv))
  print(sprintf('Using median filter %s', use_filter))

  if (!file.exists(BASE_PATH)) {
    stop('Given input file ', BASE_PATH, ' does not exist!')
  }

  if (!dir.exists(OUTPUT_PATH)) {
    print(sprintf('Creating output directory %s', OUTPUT_PATH))
    dir.create(OUTPUT_PATH, recursive = TRUE)
  }

  config <- data.frame(
    base = BASE_PATH,
    output = OUTPUT_PATH,
    is_tsv = is_tsv,
    file_name = OUTPUT_NAME,
    use_filter = use_filter
  )
  return(config)
}

get_as_order <- function(data, old_order) {
  as_order <- old_order
  as_clients <- data %>% group_by(AS, index) %>% summarize()
  for (row in 1:nrow(as_clients)) {
    asn <- as_clients[row, "AS"]
    if (!asn %in% as_order) {
      as_order <- append(as_order, asn$AS)
    }
  }
  as_order <- rev(as_order)
  return(as_order)
}

load_destinations <- function(destination_top, tsv=FALSE) {

  if (tsv) {
    print("Reading TSV file")
    destination_top <- read.table(destination_top)
    colnames(destination_top) <- c("index", "perc", "AS")
  } else {
    print("Reading CSV file")
    destination_top <- read.csv(destination_top)
    colnames(destination_top) <- c("index", "AS", "perc", "max_target", "p_relay")
  }

  min_max <- destination_top %>%
    mutate(perc = as.numeric(perc)) %>%
    group_by(index, AS) %>%
    summarize(n = n(), min = min(as.numeric(perc)), max = max(as.numeric(perc)), mean = mean(perc), median = median(perc)) %>%
    mutate(old = AS %in% DESTINATION_OLD_ORDER)

  destination_min_maxed <- left_join(destination_top, min_max, by = c('index', 'AS'))
  return(destination_min_maxed)
}

plot_destinations <- function(destination_top, tsv = FALSE) {
  destination_min_maxed <- load_destinations(destination_top, tsv)

  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(y_label = "Number of AS", x_label = "Exit Probability")

  as_order <- get_as_order(destination_min_maxed, DESTINATION_OLD_ORDER)

  plot <- destination_min_maxed %>%
    filter(old | n > 0) %>%
    mutate(AS = factor(AS, levels = as_order)) %>%
    ggplot(aes(x = perc, y = AS)) +
    geom_point(size = 3) +
    geom_errorbar(aes(x = perc, xmax = max, xmin = min), na.rm = TRUE) +
    geom_text(aes(label = n, x = 1.1), size = 5) +
    scale_x_continuous(breaks = c(0.0, 0.25, 0.5, 0.75, 1.0)) +
    coord_cartesian(xlim = c(0, 1.1)) +
    eris_labs +
    eris_theme +
    eris_grid

  return(plot)
}

plot_destinations_data <- function(destination_min_maxed) {
  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(y_label = "Involved AS", x_label = "Exit Probability")

  as_order <- get_as_order(destination_min_maxed, DESTINATION_OLD_ORDER)

  plot <- destination_min_maxed %>%
    filter(old | n > 0) %>%
    mutate(AS = factor(AS, levels = as_order)) %>%
    ggplot(aes(x = perc, y = AS)) +
    geom_point(size = 3) +
    geom_errorbar(aes(x = perc, xmax = max, xmin = min), na.rm = TRUE) +
    geom_text(aes(label = n, x = 1.1), size = 5) +
    scale_x_continuous(breaks = c(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), labels = percent) +
    geom_vline(xintercept = 0.2, color = "red") +
    coord_cartesian(xlim = c(0, 1.1)) +
    eris_labs +
    eris_theme +
    eris_grid

  return(plot)
}

plot_destinations_data_shifted <- function(destination_min_maxed) {
  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(y_label = "Involved AS", x_label = "Exit Probability")

  as_order <- get_as_order(destination_min_maxed, DESTINATION_OLD_ORDER)

  plot <- destination_min_maxed %>%
    filter(old | n > 0) %>%
    mutate(AS = factor(AS, levels = as_order)) %>%
    ggplot(aes(x = perc, y = AS)) +
    facet_wrap(~dataset, nrow = 1) +
    geom_point(size = 3) +
    geom_errorbar(aes(x = perc, xmax = max, xmin = min), na.rm = TRUE) +
    geom_text(aes(label = n, x = 1.1), size = 5) +
    scale_x_continuous(breaks = c(0.0, 0.2, 0.4, 0.6, 0.8, 1.0), labels = percent) +
    geom_vline(xintercept = 0.2, color = "red") +
    coord_cartesian(xlim = c(0, 1.15))
    eris_labs +
    eris_theme +
    eris_grid

  return(plot)
}

if (FALSE) {
  scan_2020_ipv4 <- "~/coding/work/room5/2022_ripe_tor_cose/paper-source/tables/destination-top/destination-top.dat"
  plot <- plot_destinations(scan_2020_ipv4, tsv = TRUE)
  plot_save_square("/home/havok/Documents/ripetor/images_2020/destination", '/2020_destination-top.pdf', plot)

  scan_2022_ipv4_de <- "~/Documents/ripetor/destination-top/de_ipv4/destination-top.dat"
  plot_destinations(scan_2022_ipv4_de)

  scan_2022_ipv4_us <- "~/Documents/ripetor/destination-top/us_ipv4/destination-top.dat"
  plot_destinations(scan_2022_ipv4_us)

  scan_2022_ipv6_de <- "~/Documents/ripetor/destination-top/de_ipv6/destination-top.dat"
  plot_destinations(scan_2022_ipv6_de)

  scan_2022_ipv6_us <- "~/Documents/ripetor/destination-top/us_ipv6/destination-top.dat"
  plot_destinations(scan_2022_ipv6_us)

  scan_2022_ipv4_us <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/destinations/destination_us_ipv4.dat"
  scan_2022_ipv4_us <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/destinations/destination_us_ipv6.dat"

  destination_min_maxed <- load_destinations(scan_2022_ipv4_us)
  filtered_destinations <- destination_min_maxed %>% filter(old | median > 0.01)
  filtered_destinations <- destination_min_maxed %>% filter(old | mean > 0.05)

  plot_destinations_data(destination_min_maxed)
  plot_destinations_data(filtered_destinations)
  filtered_destinations %>%
    group_by(index, AS, max_target, p_relay) %>%
    summarize(value = max(perc)) %>%
    arrange(desc(value))


  scan_2020_ipv4_us <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/destinations/destination_us_2020_ipv4.dat"
  scan_2020_ipv4_us_data <- load_destinations(scan_2020_ipv4_us) %>% mutate(dataset = "2020 IPv4")
  scan_2022_ipv4_us <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/destinations/destination_us_ipv4.dat"
  scan_2022_ipv4_us_data <- load_destinations(scan_2022_ipv4_us) %>% mutate(dataset = "2022 IPv4")
  scan_2022_ipv6_us <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/destinations/destination_us_ipv6.dat"
  scan_2022_ipv6_us_data <- load_destinations(scan_2022_ipv6_us) %>% mutate(dataset = "2022 IPv6")
  destination_data <- rbind(scan_2020_ipv4_us_data, scan_2022_ipv4_us_data, scan_2022_ipv6_us_data)
  destination_data <- destination_data %>% filter(old | median > 0.01)
  plot <- plot_destinations_data_shifted(destination_data)
  plot_save_variable("/home/havok/Documents/ripetor/images_gabriel/", 'destinations-top-shifted.pdf', plot, 4500, 1800)
}

config <- load_destination_paths()
destination_min_maxed <- load_destinations(config$base, tsv = config$is_tsv)
if (config$use_filter) {
  destination_min_maxed <- destination_min_maxed %>% filter(old | median > 0.01)
}
plot <- plot_destinations_data(destination_min_maxed)
plot_save_square(config$output, config$file_name, plot)
