#####################################################################
# These functions are used to plot our graphs with consistent sizes
# Markus 06.07.2022
#####################################################################

plot_save_variable <- function(image_path, filename, plot, width, height) {
  ggsave(
    filename = filename,
    plot = plot,
    path = image_path,
    width = width,
    height = height,
    units = "px",
    device = "pdf"
  )
  print(paste0("Stored file at path ", filename))
}

plot_save <- function(image_path, filename, plot) {
  plot_save_variable(image_path, filename, plot, ERIS_DEFAULT_WIDTH, ERIS_DEFAULT_HEIGHT)
}

plot_save_square <- function(image_path, filename, plot) {
  plot_save_variable(image_path, filename, plot, ERIS_DEFAULT_WIDTH, ERIS_DEFAULT_WIDTH)
}

plot_save_wide <- function(image_path, filename, plot) {
  plot_save_variable(image_path, filename, plot, ERIS_DEFAULT_WIDE, ERIS_DEFAULT_HEIGHT)
}

print("Loading Plot Storage DONE")