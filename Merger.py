from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import io

app = Flask(__name__)
CORS(app)  # Allow frontend requests


@app.route("/merge", methods=["POST"])
def merge_pdfs():
    files = request.files.getlist("files")
    if not files:
        return {"error": "No files uploaded"}, 400

    merger = PdfMerger()
    for f in files:
        merger.append(f)

    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)

    return send_file(output,
                     as_attachment=True,
                     download_name="merged.pdf",
                     mimetype="application/pdf")


@app.route("/secondlast", methods=["POST"])
def merge_second_last_pages():
    files = request.files.getlist("files")
    if not files:
        return {"error": "No files uploaded"}, 400

    writer = PdfWriter()

    for f in files:
        try:
            reader = PdfReader(f)
            if len(reader.pages) >= 2:
                second_last_page = reader.pages[-2]  # ✅ get second last page
                writer.add_page(second_last_page)
        except Exception as e:
            print(f"❌ Skipped {f.filename}: {e}")

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    return send_file(output,
                     as_attachment=True,
                     download_name="second_last_pages.pdf",
                     mimetype="application/pdf")

@app.route('/unlock', methods=['POST'])
def unlock_pdf():
    try:
        # Get the uploaded file
        pdf_file = request.files['file']
        password = request.form.get('password', '')
        
        # Read the PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Check if PDF is encrypted
        if pdf_reader.is_encrypted:
            # Try to decrypt with provided password
            if password:
                decrypt_success = pdf_reader.decrypt(password)
                if not decrypt_success:
                    return {"error": "Incorrect password"}, 400
            else:
                return {"error": "PDF is encrypted but no password provided"}, 400
        
        # Create a new PDF writer
        pdf_writer = PyPDF2.PdfWriter()
        
        # Add all pages to the writer
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Create a bytes buffer for the new PDF
        output_buffer = io.BytesIO()
        
        # Write the unlocked PDF to the buffer
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        # Return the unlocked PDF
        return send_file(
            output_buffer,
            as_attachment=True,
            download_name='unlocked.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return {"error": str(e)}, 500
    
@app.route('/calculate-emi', methods=['POST'])
def calculate_emi():
    try:
        data = request.get_json()
        
        loan_amount = float(data['loanAmount'])
        interest_rate = float(data['interestRate'])
        loan_tenure = float(data['loanTenure'])
        tenure_type = data.get('tenureType', 'years')
        
        # Convert to months if tenure is in years
        if tenure_type == 'years':
            loan_tenure = loan_tenure * 12
        
        # Calculate monthly interest rate
        monthly_interest_rate = interest_rate / 12 / 100
        
        # Calculate EMI
        emi = loan_amount * monthly_interest_rate * \
              math.pow(1 + monthly_interest_rate, loan_tenure) / \
              (math.pow(1 + monthly_interest_rate, loan_tenure) - 1)
        
        # Calculate total values
        total_payment = emi * loan_tenure
        total_interest = total_payment - loan_amount
        
        return jsonify({
            'monthlyEmi': round(emi, 2),
            'totalInterest': round(total_interest, 2),
            'totalPayment': round(total_payment, 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
