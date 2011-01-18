import sys, os, shutil
import Image, ImageEnhance

def fill_width(maxwidth, width, height):
    ratio = float(maxwidth)/float(width)
    return (int(width * ratio), int(height * ratio))

def is_landscape(image):
    width, height = image.size 
    return width/height > 0

def process_image(source, destination):
    constant_width = 744
    try:
        # convert to black and white
        image = Image.open(source, "r").convert("L")

        # rotate the image if it's a double-page
        if is_landscape(image):
            image = image.transpose(Image.ROTATE_90)

        # Resize the image to fit on a kindle.
        image = image.resize(fill_width(constant_width, *image.size), Image.ANTIALIAS)

        # Do some slight sharpening.
        image = ImageEnhance.Sharpness(image).enhance(2)

        image.save(destination)

        return True
    except:
        print "invalid file, removing", source
        #os.remove(source)
        return False

def check_file(file):
    return os.access(file, os.F_OK)

def make_dir(dir):
    if False == os.access(dir, os.F_OK):
        try:
            os.makedirs(dir, 0777)
        except OSError:
            pass

def get_filelist(path):
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

from subprocess import *
def run_command_with_status_params(Command, Params, Verbose = True, Env = None):
    if Verbose:
        print([Command] + Params)
    sys.stdout.flush()
    try:
        p = Popen([Command] + Params, bufsize=0, stderr=STDOUT, stdout=PIPE, env=Env)
        output = p.stdout
        err_output = p.stderr
        pid = p.pid

        outdata = []
        for line in iter(output.readline, ''):
            if Verbose:
                print line,

            outdata.append(line)
            sys.stdout.flush() 
        
        exitcode = p.wait()
        return (exitcode, outdata)

    except Exception, inst:
        print inst.args
        sys.stdout.flush() 
        sys.stderr.flush() 
        pass
    return (1,[])
    

import shlex
def run_command_with_status(Command, Verbose = True):
    args = shlex.split(Command)
    CommandName = args[0]
    Args = args[1:]
    return run_command_with_status_params(CommandName, Args, Verbose)

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

def create_pdf(image_paths, output_filepath):
    image_paths.sort()
    pdf = Canvas(output_filepath)
    pdf.setAuthor("ComicConverter")
    for image_path in image_paths:
        image = Image.open(image_path)
        width, height = A4
        pdf.drawInlineImage(image, x=0, y=0, width=width, height=height)
        pdf.showPage()
    pdf.save()


input_path = "comics"
unpack_path = "unpacked"
cache_path = "processing"
output_path = "processed"
make_dir(output_path)

chapters = [1]

def unpack(filepath, comic_title, tempfolder):
    supported_formats = {
                        "cbr": "rar", 
                        "cbz": "zip", 
                        "cb7": "7z"}

    fileformat = filepath.split(".")[-1]

    supported_format = supported_formats[fileformat]

    unpack_path = os.path.join(tempfolder, supported_format, comic_title)
    make_dir(unpack_path)

    command = ""
    if supported_format == "rar":
        command = "unrar e \"%s\" \"%s\"" % (filepath, unpack_path)
    elif supported_format == "zip":
        command = "unzip -j \"%s\" -d \"%s\"" % (filepath , unpack_path)

    if len(command) > 0:
        run_command_with_status(command)

    return unpack_path


for comic in get_filelist(input_path):

    filename = ".".join(os.path.basename(comic).split(".")[:-1])
    comic_title = "_".join(filename.split(" "))

    document_filepath = "%s/%s.pdf" % (output_path, comic_title)
    if check_file(document_filepath):
        print "skipped", document_filepath
        continue

    comic_cache_path = unpack(os.path.join(input_path, comic), comic_title, unpack_path)

    print "Processing %s" % (comic_title)
    image_paths = []
    valid = False
    for filename in get_filelist(comic_cache_path):
        imagename = ".".join(filename.split(".")[:-1]) + ".jpg"

        input_filename = os.path.join(comic_cache_path, filename)
        output_filename = os.path.join(cache_path, imagename)
        make_dir(cache_path)

        if not process_image(input_filename, output_filename):
            valid = False
        else:
            valid = True
            image_paths.append(output_filename)

    if valid:
        create_pdf(image_paths, document_filepath)
        print "Done"
    else:
        print "Invalid"

