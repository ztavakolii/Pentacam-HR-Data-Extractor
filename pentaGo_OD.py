from pywinauto import Application , Desktop, mouse
from pywinauto.keyboard import send_keys
from pywinauto.timings import wait_until , Timings
import pyautogui
import time
import os
from datetime import datetime

def examinations_list_updated(examinations_list,old_ids): # examinations_list is a DataGridView
    new_rows = examinations_list.children(control_type="Custom")
    if len(new_rows)<=1:
        return False
    new_ids = [r.element_info.element for r in new_rows]
    return new_ids != old_ids



def popup_menu_exists():
    try:
        popup = Desktop(backend="uia").window(class_name="#32768") 
        return popup.exists() and popup.is_visible()
    except:
        return False
    

    
def error_window_exists(): # possible error that may occur after clicking the Pentacam button
    try:
        err_win = Desktop(backend="win32").window(class_name="#32770")  
        return err_win.exists() and err_win.is_visible()
    except:
        return False
    

Timings.after_sendkeys_key_wait=0
pyautogui.PAUSE=0


# start the app
app=Application(backend="uia").start("C:\\Pentacam\GO.exe") # change program path based on yours
main_window=app.window(title="OCULUS  -  Patient Data Management")

patients_list=main_window.child_window(title="DataGridView", auto_id="DataGridView_Patients", control_type="Table")

rows = patients_list.children(control_type="Custom")
print(f"\nNumber of patients: {len(rows)-1}")
number_of_pre_patients=2186
print('number of previous patients ', number_of_pre_patients)


patients_list.type_keys("{HOME}")
patients_list.type_keys("{DOWN 51}")

for i in range(53,len(rows)):
    try:
        if i > 13:
            patients_list.type_keys("{DOWN}")
        # wait for updating examinations DataGridView
        examinations_list=main_window.child_window(title="DataGridView", auto_id="DataGridView_ExaminationList", control_type="Table")
        time.sleep(1)

        old_rows=examinations_list.children(control_type="Custom")
        old_ids=[r.element_info.element for r in old_rows]

        rows[i].click_input()
        try:
            wait_until(timeout=10, retry_interval=0.1, func=examinations_list_updated,examinations_list=examinations_list,old_ids=old_ids)
        except:
            print('One exception occured at line 54.')
            continue
        # get patient's examinations and select last examination for each eye
        rows2 = [c for c in examinations_list.children(control_type="Custom") if c.element_info.name != "Top Row"]

        groups = {"right": []}

        for row in rows2:
            cells = row.children(control_type="DataItem")

            try:
                number = int(cells[0].legacy_properties().get("Value"))
            except ValueError:
                print('One exception occured at line 66.')
                continue

            eye_value = cells[4].legacy_properties().get("Value").lower()

            if eye_value in groups:
                groups[eye_value].append((number, row))


        for key, items in groups.items():
            if items: 
                
                    _, target_row = max(items, key=lambda x: x[0])

                    cells=target_row.children(control_type="DataItem")
            

                    target_row.click_input()
                
                    # start pentacam app
                    pentacam_button=main_window.child_window(title="Pentacam", auto_id="btn_Device1", control_type="Button")
                    pentacam_button.click_input()

                    # close "No communication with pentacam" error window
                    try:
                        
                        err_win = Desktop(backend="win32").window(class_name="#32770")
                        err_win.child_window(title="OK", class_name="Button").click_input()
                    except:
                        print('One exception occured at line 88.')


                    # make directory for patient's data
                    base_dir = "D:\dat1"  # change storage directory based on your path
                    patient_id = str(i+ number_of_pre_patients)
                   
                    patient_id+='\OD'

                    temp=patient_id+"\densito"
                    patient_dir = os.path.join(base_dir, temp)
                    os.makedirs(patient_dir, exist_ok=True)

                    temp=patient_id+"\\ref"
                    patient_dir = os.path.join(base_dir, temp)
                    os.makedirs(patient_dir, exist_ok=True)

                    
                    base_dir = "D:\dat2"  # change storage directory based on your path
                    patient_id = str(i + number_of_pre_patients)
                   
                    patient_id+='\OD'
                    patient_dir = os.path.join(base_dir, patient_id)
                    os.makedirs(patient_dir, exist_ok=True)

                    
                    time.sleep(1.5)
            
                    # change storage paths in pentacam app
                    app2=Application(backend="uia").connect(path="C:\\Pentacam\PENTACAM.exe")
                    general_overview=app2.window(title="OCULUS  -  PENTACAM   General Overview")

                    try:
                        general_overview.menu_select("Display->Corneal Optical Densitometry")
                    except:
                        mouse.click(coords=(230,50),button='left')
                        mouse.click(coords=(450,475),button='left')

                    corneal_densitometry=app2.window(title="OCULUS  -  PENTACAM   Corneal Optical Densitometry")
                    # Anterior layer densitometry picture -> in 108 micro meter
                    mouse.click(coords=(796,210),button='left')
                    mouse.click(coords=(804,210),button='left')
                    time.sleep(3) # 5s
                
                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    dlg=corneal_densitometry.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat1" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                    
                    file_path+='\OD'
                    file_path+="\densito\\anterior.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")
                    

                    # Center layer densitometry picture
                    #for layer2 slider
                    layer2_checkbox=corneal_densitometry.child_window(control_type="CheckBox")
                    layer2_checkbox.click_input()
                    mouse.press(coords=(804,250),button='left')
                    mouse.move(coords=(828,250))
                    mouse.release(coords=(828,250),button='left')
                    time.sleep(3) # 5s

                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    dlg=corneal_densitometry.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat1" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                    
                    file_path+='\OD'
                    file_path+="\densito\center.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")

                    # Posterior layer densitometry picture
                    # for layer1 slider
                    mouse.press(coords=(804,210),button='left')
                    mouse.move(coords=(828,210))
                    mouse.release(coords=(828,210),button='left')
                    # for layer2 slider
                    mouse.press(coords=(828,250),button='left')
                    mouse.move(coords=(830,250))
                    mouse.release(coords=(830,250),button='left')
                    time.sleep(3) # 5s

                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    dlg=corneal_densitometry.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat1" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                   
                    file_path+='\OD'
                    file_path+="\densito\posterior.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")

                    # save reference images
                    try:
                        corneal_densitometry.menu_select("Display->4 Maps Selectable")
                    except:
                        mouse.click(coords=(230,50),button='left')
                        mouse.click(coords=(475,165),button='left')

                    time.sleep(3) # 5s
                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    four_maps_selectable=app2.window(title="OCULUS  -  PENTACAM   4 Maps Selectable")
                    dlg=four_maps_selectable.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat1" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                    
                    file_path+='\OD'
                    file_path+="\\ref\\4 map.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")


                    # belin/ambrisio enhanced display
                    try:
                        four_maps_selectable.menu_select("Display->Belin/Ambrósio Enhanced Ectasia Display")
                    except:
                        mouse.click(coords=(230,50),button='left')
                        mouse.click(coords=(410,815),button='left')

                    time.sleep(3) # 5s
                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    belin=app2.window(title="OCULUS  -  PENTACAM   Belin/Ambrósio Enhanced Ectasia Display")
                    dlg=belin.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat1" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                    
                    file_path+='\OD'
                    file_path+="\\ref\\belin.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")


                    # topometric/kc-staging
                    try:
                        belin.menu_select("Display->Topometric/KC-Staging")
                    except:
                        mouse.click(coords=(230,50),button='left')
                        mouse.click(coords=(400,515),button='left')

                    time.sleep(3) # 5s
                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    KC_staging=app2.window(title="OCULUS  -  PENTACAM   Topometric/KC-Staging")
                    dlg=KC_staging.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat1" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                    
                    file_path+='\OD'
                    file_path+="\\ref\kc-staging.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")



                    # 4 maps refractive display
                    try:
                        KC_staging.menu_select("Display->4 Maps Refractive")
                    except:
                        mouse.click(coords=(230,50),button='left')
                        mouse.click(coords=(490,200),button='left')

                    time.sleep(3) # 5s
                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    four_maps_refractive=app2.window(title="OCULUS  -  PENTACAM   4 Maps Refractive")
                    dlg=four_maps_refractive.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat2" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                    
                    file_path+='\OD'
                    file_path+="\\4 map.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")


                    # belin/ambrisio enhanced display
                    try:
                        four_maps_refractive.menu_select("Display->Belin/Ambrósio Enhanced Ectasia Display")
                    except:
                        mouse.click(coords=(230,50),button='left')
                        mouse.click(coords=(410,815),button='left')

                    time.sleep(3) # 5s
                    mouse.click(coords=(1838,50),button='left')
                    mouse.click(coords=(1780,80),button='left')

                    belin=app2.window(title="OCULUS  -  PENTACAM   Belin/Ambrósio Enhanced Ectasia Display")
                    dlg=belin.child_window(title_re="Export Current Screen Image")

                    file_path=r"D:\dat2" # change path based on yours
                    file_path+="\\"
                    file_path+=str(i + number_of_pre_patients)

                    
                    file_path+='\OD'
                    file_path+="\\belin.JPG"
                
                    file_name=dlg.child_window(title="File name:", auto_id="1001", control_type="Edit")

                    file_name.click_input()
                    send_keys("{HOME}+{END}{BACKSPACE}")
                    send_keys(file_path)
                    send_keys("{ENTER}")


                    mouse.click(coords=(1880,15),button='left')

                    if main_window.is_minimized():
                        main_window.restore()
                    main_window.set_focus()

    except:
        continue
  

                


                















        

        


        








