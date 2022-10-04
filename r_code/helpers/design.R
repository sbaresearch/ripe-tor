#####################################################
# This file contains general theming for all graphs
# Markus 06.07.2022
#####################################################

### Defaults
# Breaks
default_breaks <- 10^(0:10)
default_minor_log10_breaks <- rep(1:9, 21) * (10^rep(-10:10, each = 9))

# Plot
ERIS_DEFAULT_WIDTH <- 2000
ERIS_DEFAULT_WIDE <- 3000
ERIS_DEFAULT_HEIGHT <- 1200
default_height_wide <- 800

# Color codes
ggplot_default_ipv4 <- "#F8766D"
ggplot_default_ipv6 <- "#00BFC4"

# taken from https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=3
# colorblind AND printerfriendly for quantitive data only has four colors

ERIS_COLOR_ONE <- "#a6cee3"
ERIS_COLOR_TWO <- "#1f78b4"
ERIS_COLOR_THREE <- "#33a02c"
ERIS_COLOR_FOUR <- "#b2df8a"
ERIS_COLOR_FIVE <- "#fb9a99" # from five colors on it is NOT colorblind friendly anymore :(

ERIS_IPV4 <- ERIS_COLOR_THREE
ERIS_IPV6 <- ERIS_COLOR_ONE

ERIS_COLORS_COL <- c(ERIS_COLOR_ONE, ERIS_COLOR_TWO, ERIS_COLOR_THREE, ERIS_COLOR_FOUR)
ERIS_TWO_COLORS <- c(ERIS_IPV4, ERIS_IPV6)
ERIS_TWO_DOUBLE <- c(ERIS_IPV4, ERIS_IPV4, ERIS_IPV6, ERIS_IPV6)

# LineType
ggplot_line_full <- 1
ggplot_line_dashed <- 2
ggplot_line_dotted <- 3
ggplot_dotdash <- 4
ggplot_longdash <- 5
ggplot_twodash <- 6

# get element_blank or element_text with given setting based on a boolean decider
get_element_blank_or_size <- function(decider, size) {
  if (decider) {
    return(element_blank())
  }
  return(element_text(size = size))
}

get_element_blank_or_default <- function(decider, default) {
  if (!decider) {
    return(element_blank())
  }
  return(default)
}


# get default eris theme with some flexibility
get_eris_theme <- function(
  legend_position = "bottom", hide_legend_title = TRUE, hide_plot_title = TRUE,
  hide_y_label_title = FALSE, hide_x_label_title = FALSE, large_legend_key = FALSE,
  x_angle = 0, y_angle = 0, bw_theme = FALSE
) {

  legend_title <- get_element_blank_or_size(hide_legend_title, 14)
  plot_title <- get_element_blank_or_size(hide_plot_title, 16)
  axis_x_label <- get_element_blank_or_size(hide_x_label_title, 14)
  axis_y_label <- get_element_blank_or_size(hide_y_label_title, 14)

  eris_theme <- theme(
    plot.title = plot_title,
    axis.text.x = element_text(size = 12, angle = x_angle),
    axis.title.x = axis_x_label,
    axis.text.y = element_text(size = 12, angle = y_angle),
    axis.title.y = axis_y_label,
    legend.position = legend_position,
    legend.text = element_text(size = 12),
    legend.title = legend_title,
    strip.text.x = element_text(size = 16),
    strip.text.y = element_text(size = 16)
  )

  if (bw_theme) {
      return(theme_bw() + eris_theme)
  }

  return(eris_theme)
}

# get eris labs with defaults set to blank
get_eris_labs <- function(
  overall_title = "", x_label = "", y_label = ""
) {
  return(labs(
    title = overall_title,
    x = x_label,
    y = y_label
  ))
}

get_eris_grid <- function(
  line_color = "gray75", line_size = 0.5, linetype = 1,
  enable_major_x = TRUE, enable_minor_x = FALSE,
  enable_major_y = TRUE, enable_minor_y = FALSE
) {

  line <- element_line(color = line_color, size = line_size, linetype = linetype)
  major_x <- get_element_blank_or_default(enable_major_x, line)
  minor_x <- get_element_blank_or_default(enable_minor_x, line)
  major_y <- get_element_blank_or_default(enable_major_y, line)
  minor_y <- get_element_blank_or_default(enable_minor_y, line)

  return(theme(
    panel.grid.major.x = major_x,
    panel.grid.minor.x = minor_x,
    panel.grid.major.y = major_y,
    panel.grid.minor.y = minor_y
  ))
}

print("Loading ERIS Design DONE")