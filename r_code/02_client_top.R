#!/usr/bin/env Rscript

print("Loading dependencies")
source("00_sources.R")

CLIENT_ORDER <- c(
  "AS174", "AS1200", "AS1273", "AS1299", "AS2914", "AS3257", "AS3356", "AS6453", "AS6830", "AS6939", "AS9002",
  "AS20764", "AS201011")

load_client_paths <- function() {
  parser <- arg_parser("Generate client-top graphs")
  parser <- add_argument(parser, "--base_path", short = "-b", help = "Path containing both client-top-de.dat and client-top-us.dat")
  parser <- add_argument(parser, "--output_path", short = "-o", help = "Path to store output files")
  parser <- add_argument(parser, "--use_tsv", short = "-t", flag=TRUE, help = "Read files as old TSV files")
  parser <- add_argument(parser, "--no_ru", short = "-x", flag=TRUE, help = "Exclude reading RU file")
  parser <- add_argument(parser, "--only_ru", short = "-r", flag=TRUE, help = "Only read RU file")
  args <- parse_args(parser)

  BASE_PATH <- normalizePath(args$base_path, mustWork = FALSE)
  OUTPUT_PATH <- normalizePath(args$output_path, mustWork = FALSE)
  is_tsv <- args$use_tsv
  no_ru <- args$no_ru
  only_ru <- args$only_ru

  print(sprintf('Using base path %s', BASE_PATH))
  print(sprintf('Using output path %s', OUTPUT_PATH))
  print(sprintf('Using TSV reader %s', is_tsv))
  print(sprintf('No RU %s', no_ru))
  print(sprintf('Only RU %s', only_ru))

  if (!dir.exists(BASE_PATH)) {
    stop('Given base path ', BASE_PATH, ' does not exist!')
  }

  if (!dir.exists(OUTPUT_PATH)) {
    print(sprintf('Creating output directory %s', OUTPUT_PATH))
    dir.create(OUTPUT_PATH, recursive = TRUE)
  }

  config <- data.frame(
    base = BASE_PATH,
    output = OUTPUT_PATH,
    is_tsv = is_tsv,
    no_ru = no_ru,
    only_ru = only_ru

  )
  return(config)
}

load_client_data_no_ru <- function(base_path, tsv=TRUE) {
  client_top_de_file <- paste0(base_path, "/client-top-de.dat")
  client_top_us_file <- paste0(base_path, "/client-top-us.dat")

  if (tsv) {
    print("Reading TSV file")
    client_top_de <- read.table(client_top_de_file, header = FALSE) %>% mutate(type = "DE")
    client_top_us <- read.table(client_top_us_file, header = FALSE) %>% mutate(type = "US")
  } else {
    print("Reading CSV file")
    client_top_de <- read.csv(client_top_de_file, header = FALSE) %>% mutate(type = "DE")
    client_top_us <- read.csv(client_top_us_file, header = FALSE) %>% mutate(type = "US")
  }

  clients <- rbind(client_top_de, client_top_us)
  colnames(clients) <- c("index", "AS", "perc", "max_target", "p_relay", "type")

  # add lines for AS without any lines for a specific country
  # otherwise the position_dodge does nothing as there is nothing to dodge
  as_clients <- clients %>% group_by(AS, index) %>% summarize()
  for (row in 1:nrow(as_clients)) {
    asn <- as_clients[row, "AS"]
    index <- as_clients[row, "index"]
    number_lines_us <- clients %>% filter(AS == asn$AS, type == "US")
    number_lines_de <- clients %>% filter(AS == asn$AS, type == "DE")
    number_lines_us <- nrow(number_lines_us)
    number_lines_de <- nrow(number_lines_de)

    if (number_lines_us == 0) {
      print("AS needs lines for US!")
      add_line <- c(index$index, asn$AS, 10, 0, 0, "US")
      clients <- rbind(clients, add_line)
    }

    if (number_lines_de == 0) {
      print("AS needs lines for DE!")
      add_line <- c(index$index, asn$AS, as.numeric(10), 0, 0, "DE")
      clients <- rbind(clients, add_line)
    }

  }

  clients <- clients %>%
    mutate(perc = as.numeric(perc))

  number_lines <- clients %>%
    filter(perc <= 1) %>%
    group_by(AS, type) %>%
    summarize(n = n())

  min_max <- clients %>%
    group_by(type, AS) %>%
    summarize(min = min(as.numeric(perc)), max = max(as.numeric(perc)))

  min_max <- left_join(min_max, number_lines, by = c('AS', 'type'))

  hide_empty <- min_max %>%
    group_by(AS) %>%
    summarize(sum_n = sum(n), as_min = min(min), as_max = max(max), old = AS %in% CLIENT_ORDER) %>%
    mutate(show = (sum_n >= 1) | old)

  min_max <- inner_join(min_max, hide_empty, by = c('AS'))

  clients_min_maxed <- inner_join(clients, min_max, by = c('AS', 'type')) %>%
    filter(show)

  return(clients_min_maxed)
}

load_client_data <- function(base_path, tsv=TRUE, filter=TRUE) {
  client_top_de_file <- paste0(base_path, "/client-top-de.dat")
  client_top_us_file <- paste0(base_path, "/client-top-us.dat")
  client_top_ru_file <- paste0(base_path, "/client-top-ru.dat")

  if (tsv) {
    print("Reading TSV file")
    client_top_de <- read.table(client_top_de_file, header = FALSE) %>% mutate(type = "DE")
    client_top_us <- read.table(client_top_us_file, header = FALSE) %>% mutate(type = "US")
    client_top_ru <- read.table(client_top_ru_file, header = FALSE) %>% mutate(type = "RU")
  } else {
    print("Reading CSV file")
    client_top_de <- read.csv(client_top_de_file, header = FALSE) %>% mutate(type = "DE")
    client_top_us <- read.csv(client_top_us_file, header = FALSE) %>% mutate(type = "US")
    client_top_ru <- read.csv(client_top_ru_file, header = FALSE) %>% mutate(type = "RU")
  }

  clients <- rbind(client_top_de, client_top_us, client_top_ru)
  colnames(clients) <- c("index", "AS", "perc", "max_target", "p_relay", "type")

  # add lines for AS without any lines for a specific country
  # otherwise the position_dodge does nothing as there is nothing to dodge
  as_clients <- clients %>% group_by(AS, index) %>% summarize()
  for (row in 1:nrow(as_clients)) {
    asn <- as_clients[row, "AS"]
    index <- as_clients[row, "index"]
    number_lines_us <- clients %>% filter(AS == asn$AS, type == "US")
    number_lines_de <- clients %>% filter(AS == asn$AS, type == "DE")
    number_lines_ru <- clients %>% filter(AS == asn$AS, type == "RU")
    number_lines_us <- nrow(number_lines_us)
    number_lines_de <- nrow(number_lines_de)
    number_lines_ru <- nrow(number_lines_ru)

    if (number_lines_us == 0) {
      print("AS needs lines for US!")
      add_line <- c(index$index, asn$AS, 10, 0, 0, "US")
      clients <- rbind(clients, add_line)
    }

    if (number_lines_de == 0) {
      print("AS needs lines for DE!")
      add_line <- c(index$index, asn$AS, as.numeric(10), 0, 0, "DE")
      clients <- rbind(clients, add_line)
    }

    if (number_lines_ru == 0) {
      print("AS needs lines for RU!")
      add_line <- c(index$index, asn$AS, as.numeric(10), 0, 0, "RU")
      clients <- rbind(clients, add_line)
    }
  }

  clients <- clients %>%
    mutate(perc = as.numeric(perc))

  number_lines <- clients %>%
    filter(perc <= 1) %>%
    group_by(AS, type) %>%
    summarize(n = n())

  min_max <- clients %>%
    group_by(type, AS) %>%
    summarize(min = min(as.numeric(perc)), max = max(as.numeric(perc)))

  min_max <- left_join(min_max, number_lines, by = c('AS', 'type'))

  hide_empty <- min_max %>%
    group_by(AS) %>%
    summarize(sum_n = sum(n), as_min = min(min), as_max = max(max), old = AS %in% CLIENT_ORDER) %>%
    mutate(show = (sum_n >= 6) | old)

  min_max <- inner_join(min_max, hide_empty, by = c('AS'))

  clients_min_maxed <- inner_join(clients, min_max, by = c('AS', 'type'))
  if (filter) {
    clients_min_maxed <- clients_min_maxed %>% filter(show)
  }

  return(clients_min_maxed)
}

load_client_data_only_ru <- function(base_path, tsv=TRUE, filter=TRUE) {
  client_top_ru_file <- paste0(base_path, "/client-top-ru.dat")

  if (tsv) {
    print("Reading TSV file")
    client_top_ru <- read.table(client_top_ru_file, header = FALSE) %>% mutate(type = "RU")
  } else {
    print("Reading CSV file")
    client_top_ru <- read.csv(client_top_ru_file, header = FALSE) %>% mutate(type = "RU")
  }

  clients <- rbind(client_top_de, client_top_us, client_top_ru)
  colnames(clients) <- c("index", "AS", "perc", "max_target", "p_relay", "type")

  clients <- clients %>%
    mutate(perc = as.numeric(perc))

  number_lines <- clients %>%
    filter(perc <= 1) %>%
    group_by(AS, type) %>%
    summarize(n = n())

  min_max <- clients %>%
    group_by(type, AS) %>%
    summarize(min = min(as.numeric(perc)), max = max(as.numeric(perc)))

  min_max <- left_join(min_max, number_lines, by = c('AS', 'type'))

  hide_empty <- min_max %>%
    group_by(AS) %>%
    summarize(sum_n = sum(n), as_min = min(min), as_max = max(max)) %>%
    mutate(show = (sum_n >= 6))

  min_max <- inner_join(min_max, hide_empty, by = c('AS'))

  clients_min_maxed <- inner_join(clients, min_max, by = c('AS', 'type'))
  if (filter) {
    clients_min_maxed <- clients_min_maxed %>% filter(show)
  }

  return(clients_min_maxed)
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

plot_client_data <- function(data) {
  as_order <- get_as_order(data, CLIENT_ORDER)

  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Guard Probability", y_label = "Involved AS")

  dodge_distance <- .9
  plot <- data %>%
    mutate(AS = factor(AS, levels = as_order)) %>%
    mutate(position = ifelse(type == "RU", 1.1, 1.065)) %>%
    mutate(position = ifelse(type == "US", 1.135, position)) %>%
    ggplot(aes(y = AS, x = perc, group = type, colour = type)) +
    geom_point(aes(shape = type), size = 3, position = position_dodge(width = dodge_distance)) +
    geom_errorbar(aes(y = AS, xmax = max, xmin = min), na.rm = TRUE, position = position_dodge(width = dodge_distance)) +
    geom_text(aes(label = n, x=position), position = position_dodge(dodge_distance), size = 4) +
    scale_x_continuous(breaks = c(0.0, 0.25, 0.5, 0.75, 1.0)) +
    coord_cartesian(xlim = c(0, 1.1)) +
    eris_labs +
    eris_theme +
    eris_grid
  return(plot)
}

plot_client_data_shifted <- function(data) {
  as_order <- get_as_order(data, CLIENT_ORDER)

  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Guard Probability", y_label = "Involved AS")

  dodge_distance <- .9
  plot <- data %>%
    mutate(AS = factor(AS, levels = as_order)) %>%
    mutate(position = ifelse(type == "RU", 1.1, 1.065)) %>%
    mutate(position = ifelse(type == "US", 1.135, position)) %>%
    ggplot(aes(y = AS, x = perc, group = type, colour = type)) +
    facet_wrap(~dataset, nrow = 1) +
    geom_point(aes(shape = type), size = 3, position = position_dodge(width = dodge_distance)) +
    geom_errorbar(aes(y = AS, xmax = max, xmin = min), na.rm = TRUE, position = position_dodge(width = dodge_distance)) +
    geom_text(aes(label = n, x=position), position = position_dodge(dodge_distance), size = 4) +
    scale_x_continuous(breaks = c(0.0, 0.25, 0.5, 0.75, 1.0), labels = percent) +
    coord_cartesian(xlim = c(0, 1.15)) +
    scale_color_manual(values=ERIS_COLORS_COL) +
    eris_labs +
    eris_theme +
    eris_grid
  return(plot)
}

plot_client <- function(base_path, tsv = FALSE, filter=TRUE) {
  data <- load_client_data(base_path, tsv, filter)
  plot <- plot_client_data(data)
  return(plot)
}

plot_client_boxplot <- function(base_path, tsv = FALSE) {
  data <- load_client_data(base_path, tsv)
  as_order <- get_as_order(data, CLIENT_ORDER)

  eris_theme <- get_eris_theme()
  eris_grid <- get_eris_grid()
  eris_labs <- get_eris_labs(x_label = "Guard Probability", y_label = "AS on Route")

  dodge_distance <- .9
  plot <- data %>%
    mutate(AS = factor(AS, levels = as_order)) %>%
    ggplot(aes(y = AS, x = perc, colour = type)) +
    geom_boxplot(aes(color = type)) +
    geom_text(aes(label = n, x=1.1), position = position_dodge(dodge_distance), size = 4) +
    coord_cartesian(xlim = c(0, 1.1)) +
    eris_labs +
    eris_theme +
    eris_grid
  return(plot)
}

#### Client TOP
# used for implementing and debugging the stuff
if (FALSE) {
  scan_2020_ipv4 <- "~/coding/work/room5/2022_ripe_tor_cose/paper-source/tables/client-top"
  data <- load_client_data_no_ru(scan_2020_ipv4, TRUE)
  plot <- plot_client_data(data)
  plot_save_square("/home/havok/Documents/ripetor/images_2020/client", 'client-top.pdf', plot)

  scan_2020_ipv4_new <- "~/Documents/ripetor/run_gabriel/data/client_2020"
  data <- load_client_data_no_ru(scan_2020_ipv4_new, FALSE)
  plot <- plot_client_data(data)
  plot_save_square("/home/havok/Documents/ripetor/images_2020/client", 'client-top.pdf', plot)

  scan_2022_ipv4 <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/clients/ipv4/"
  scan_2022_ipv4_data <- load_client_data(scan_2022_ipv4, FALSE) %>% mutate(dataset = "2022 IPv4")
  plot_client_data(scan_2022_ipv4_data)

  scan_2022_ipv6 <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/clients/ipv6/"
  scan_2022_ipv6_data <- load_client_data(scan_2022_ipv6, FALSE) %>% mutate(dataset = "2022 IPv6")
  plot_client_data(scan_2022_ipv6_data)

  scan_2020_ipv4_new <- "/home/havok/Documents/ripetor/run_gabriel/real_2022/clients/2020_ipv4/"
  scan_2020_ipv4_new_data <- load_client_data_no_ru(scan_2020_ipv4_new, FALSE) %>% mutate(dataset = "2020 IPv4")
  plot_client_data(scan_2020_ipv4_new_data)

  entire_set <- rbind(scan_2022_ipv4_data, scan_2022_ipv6_data, scan_2020_ipv4_new_data)
  plot <- plot_client_data_shifted(entire_set)
  plot_save_variable("/home/havok/Documents/ripetor/images_gabriel/", 'clients-top-shifted.pdf', plot, 4500, 2400)
}

# used for automated script call
config <- load_client_paths()

if (config$no_ru) {
  data <- load_client_data_no_ru(config$base, tsv = config$is_tsv, filter = FALSE)
} else if (config$only_ru) {
  data <- load_client_data_only_ru(config$base, tsv = config$is_tsv, filter = FALSE)
} else {
  data <- load_client_data(config$base, tsv = config$is_tsv, filter = FALSE)
}

plot <- plot_client_data(data)
plot_save_variable(config$output, 'client-top-unfiltered.pdf', plot, ERIS_DEFAULT_WIDTH, 4000)

data <- data %>% filter(show)
plot <- plot_client_data(data)
plot_save_square(config$output, 'client-top.pdf', plot)
