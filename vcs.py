from pdfminer import high_level
from PIL import Image
import fitz
import io
import os
from fpdf import FPDF
from datetime import datetime

#Acquiring holder information in text from PDF.
path = r'C:\Users\Yatharth\Documents\VacCert-Project\certs\uvr.pdf' #filepath: will change on deployment
text = high_level.extract_text(path)
#text is raw data from pdf, print text to view extraction
#print(text)
text = text.replace("\n\n", "%")
#print(text)
ls = text.split("%")
#print(ls)
sep = ["Beneﬁciary", "Final"]
inx = 0
for entry in ls:
    if entry.split(' ',1)[0] == sep[0] or entry.split(' ',1)[0] == sep[1]:
        break
    inx = inx + 1
ls = ls[1:]

#print(inx)
#print(ls)
#ls is list with proper entries from PDF

#dictionary for storing holder information, in order of how it is in ls
info = ["name", "age", "sex", "verif", "uhid", "refID", "vax", "dose1", "dose2", "batch1", "batch2"]
info_dict, date_batch = {}, {}

#basic info (name,age,sex,verification), hopefully this is all in order
for i in range(4):
    info_dict[info[i]] = ls[i]

#print(info_dict)

#print(len(ls[]))
#loop to sort uhid,refID,vax,dose1,dose2 (prototype: batch1,batch2)
doses, batches = [], []
bno = 1
for lsen in ls:   
    if len(lsen) > 2 and lsen[2] == '-' and "uhid" not in info_dict:
        info_dict["uhid"] = lsen
    elif len(lsen) == 14 and lsen.isdigit() and "refID" not in info_dict:
        info_dict["refID"] = lsen
    elif "vax" not in info_dict and ("COVISHIELD" in lsen or "COVAXIN" in lsen or "SPUTNIK" in lsen):
        info_dict["vax"] = lsen
    elif len(lsen) > 3 and lsen[0:2].isdigit() and lsen[3].isalpha():
        ix = lsen.find("(")
        date = lsen[:ix-1]
        batch = lsen[ix+11:-1]
        date = datetime.strptime(date, "%d %b %Y")
        date_batch[bno] = [date, batch]
        bno = bno + 1
        
doses = sorted(doses)
if date_batch[1][0] > date_batch[2][0]:
    info_dict["dose1"] = date_batch[2][0]
    info_dict["batch1"] = date_batch[2][1]
    info_dict["dose2"] = date_batch[1][0]
    info_dict["batch2"] = date_batch[1][1]
else:
    info_dict["dose1"] = date_batch[1][0]
    info_dict["batch1"] = date_batch[1][1]
    info_dict["dose2"] = date_batch[2][0]
    info_dict["batch2"] = date_batch[2][1]
#print(date_batch)
#zipped = zip(info[7:9],doses)

#for doseno,dosedt in zipped:
    #info_dict[doseno] = dosedt.strftime('%d %B %Y')

#lastly, make dummies of all entries that were left blank
for entry in info:
    if entry not in info_dict:
        info_dict[entry] = ""
#print(info_dict)

#info_dict has all holder information as a dict

#Acquiring QR code from PDF. Please leave untouched, it works as expected.
#Opening with fitz
pdf_file = fitz.open(path)
page = pdf_file[0] #only page in the pdf
image_list = page.getImageList() 
xref = image_list[0][0]
base_image = pdf_file.extractImage(xref)
image_bytes = base_image["image"]
image_ext = base_image["ext"]
qr = Image.open(io.BytesIO(image_bytes))
qr.save(open(f"qr.{image_ext}", "wb"))

#the QR has to stay this way. Several problems on the way, but we have to accomodate, since FPDF is not perfect
cwd = os.getcwd()
qr_link = cwd+'\qr.png'

#Creating new certificate with PyFPDF
def mob_1():
    #everything about the pdf the function creates, here
    hfw_img = cwd+'\imgfiles\mohfw.png'
    font_dir = cwd+r'\fonts\\'
    ph_w = 281.25
    ph_h = 500.25
    ln_y = 274
    ln_x1 = 21
    ln_x2 = 260
    pdf = FPDF('P','pt', (ph_w,ph_h))
    pdf.add_page()
    pdf.set_margins(left=0, top=0, right=0)
    pdf.add_font('Manrope','',font_dir+"Manrope-Regular.ttf",uni=True)
    pdf.add_font('ManropeBold','',font_dir+"Manrope-Bold.ttf",uni=True)
    pdf.add_font('ManropeEB','',font_dir+"Manrope-ExtraBold.ttf",uni=True)
    pdf.image(hfw_img,x=75,y=24.5,w=132,h=68,type="png")
    pdf.set_font('ManropeEB', size=11)
    pdf.set_text_color(0,0,125)
    pdf.cell(w=282,h=218,txt="COVID-19 Vaccine Certificate",border=0,align='C',ln=1)
    pdf.set_line_width(0.1)
    pdf.line(ln_x1,ln_y,ln_x2,ln_y)
    pdf.image(qr_link,x=49,y=302,w=184,h=184,type="png")
    
    pdf.set_font('Manrope', size=7) 
    pdf.set_text_color(0,0,0) 
    pdf.ln(h=96)
    pdf.cell(w=282, h=-40,txt="https://verify.cowin.gov.in",border=0,align='C',link="https://verify.cowin.gov.in",ln=2)
    #Now for any changes needed to the information dictionary. We return both objects in the end
    #1. The doses will be formatted as per the design requires
    mob_1_info = {key:info_dict[key] for key in ["name", "age", "sex", "verif", "uhid", "refID", "vax"]}
    mob_1_info["dose-batch-1"] = info_dict["dose1"].strftime('%d %B %Y')+" ("+info_dict["batch1"]+")"
    mob_1_info["dose-batch-2"] = info_dict["dose2"].strftime('%d %B %Y')+" ("+info_dict["batch2"]+")"
    #Finally, the sequence to print these details, which also has to be design-specific
    mob_1_seq = ['vax','name','age','sex','verif','uhid','refID','dose-batch-1','dose-batch-2']
    
    #creating the actual pdf object
    pdf.set_text_color(31,73,125)
    info = "Vaccine \nBeneficiary Name \nAge \nGender \nVerified ID \nUHID \nReference ID \nVaccination Dates"
    pdf.set_font('ManropeBold', size=9)
    data = ""
    for i in mob_1_seq:
        if mob_1_info[i] != "":
            data = data + mob_1_info[i] + "\n"
        else:
            data = data + "\n"
    pdf.set_xy(x=18,y=127)
    pdf.multi_cell(w=250,h=15,txt=info,align="L",border=0)
    pdf.set_xy(x=18,y=127)
    pdf.set_font('Manrope',size=9)
    pdf.set_text_color(0,0,0)
    pdf.multi_cell(w=242,h=15,txt=data,align="R",border=0)
    return pdf

des = mob_1()
des.output('mobile1.pdf','F')