from preprocessing import count_png_files, metadata_check, check_missing_files, check_image_dimensions, check_duplicate_images

real_path = "archive/Real faces"
fake_path = "archive/Fake faces"

check_missing_files()
count_png_files(real_path)
count_png_files(fake_path)
metadata_check()
check_image_dimensions()
check_duplicate_images()
