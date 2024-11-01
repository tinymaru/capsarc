# pdf.py

class PDFConfig:
    ALLOWED_EXTENSIONS = {'pdf'}


    @staticmethod
    # PDF files
    def allowed_upload_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in PDFConfig.ALLOWED_EXTENSIONS
