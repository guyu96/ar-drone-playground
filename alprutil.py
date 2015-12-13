from openalpr import Alpr


def get_alpr():
    alpr = Alpr("us", "/etc/openalpr/openalpr.conf",
                "/usr/share/openalpr/runtime_data")
    if not alpr.is_loaded():
        print("Error loading OpenALPR")
        return None
    print("Using OpenALPR" + alpr.get_version())
    return alpr


def detect_plates(alpr, img_path):
    jpeg_bytes = open(img_path, 'rb').read()
    results = alpr.recognize_array(jpeg_bytes)
    plates = results['results']
    if not plates:
        return None
    return plates


def print_plates(plates):
    plate_count = 0
    for plate in plates:
        plate_count += 1
        print("Plate #%d" % plate_count)
        print("  %12s %12s" % ("Plate", "Confidence"))

        # For each candidate for a given plate
        candidate_count = 0
        for candidate in plate['candidates']:
            candidate_count += 1
            # Print only the first 5 candidates
            if candidate_count > 5:
                break
            prefix = "-"
            if candidate["matches_template"]:
                prefix = "*"
            print("  %s %12s%12f" % (prefix, candidate['plate'],
                                     candidate['confidence']))
