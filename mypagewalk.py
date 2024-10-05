import sys
import csv

class PageWalk:
    def __init__(self, cr3, ept_ptr, ept_tables_file):
        self.cr3 = cr3
        self.ept_ptr = ept_ptr
        self.ept_tables = self.load_ept_tables(ept_tables_file)
        self.current_address = None #Remnant
        self.current_table_level = 0  # Variable to track the current table level
        self.page_miss_cnt = 0  # Variable to track the page misses if there are 2 then its a page fault

    def load_ept_tables(self, ept_tables_file): #Utilize a Dictionary (this will simplify the error detection process)
        ept_tables = {}
        with open(ept_tables_file, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Get column headers
            for header in headers:
                ept_tables[header] = []

            for row in reader:
                for i, value in enumerate(row):
                    ept_tables[headers[i]].append(value.strip())
        return ept_tables

    def translate_virtual_to_physical(self, virtual_address, cr3=None, recursion_depth=0, last_address=None):
        #print("------------PageWalk Translation------------")
        if recursion_depth == 2:  # Maximum recursion depth to avoid infinite recursion
            return "Page fault: Maximum recursion depth reached"

        if cr3 is None:
            cr3 = self.cr3

        #print("Virtual Address: " + str(hex(virtual_address)))

        pml4_index = (virtual_address >> 39) & 0x1FF
        #print("pml4 index: " + str(int(hex(pml4_index), 16)))

        pdpt_index = (virtual_address >> 30) & 0x1FF
        #print("pdpt index: " + str(int(hex(pdpt_index), 16)))

        pd_index = (virtual_address >> 21) & 0x1FF
        #print("pd index: " + str(int(hex(pd_index), 16)))

        pt_index = (virtual_address >> 12) & 0x1FF
        #print("pt index: " + str( int(hex(pt_index), 16)))

        offset = virtual_address & 0xFFF
        #print("offset: " + str(hex(offset)))

        #print("Current Register: " + str(cr3))

        self.current_table_level = 0
        
        try:
            #print(self.ept_tables[cr3])
            pml4_entry = int(cr3, 16) #Entries are the Addresses           
            current_address = pml4_entry
            #print("pml4 address: " + str(hex(pml4_entry)))
            

            #pml4_address = int(self.ept_tables[hex(int(cr3,16 ))][pml4_index],16)
            #pml4_address = self.ept_tables[cr3]
            #pml4_entry = int(self.ept_tables[cr3][pml4_index], 16)

            pdpt_entry = int(self.ept_tables[hex(pml4_entry)][pml4_index], 16) 
            self.current_table_level += 1
            current_address = pdpt_entry
            #print("pdpt address: " + str(hex(pdpt_entry)))
            
            
            pd_entry = int(self.ept_tables[hex(pdpt_entry)][pdpt_index], 16)
            self.current_table_level += 1
            current_address = pd_entry
            #print("pd address: " + str(hex(pd_entry)))
            
            
            pt_entry = int(self.ept_tables[hex(pd_entry)][pd_index], 16)
            self.current_table_level += 1
            current_address = pt_entry
            #print("pt address: " + str(hex(pt_entry)))
            
            physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
            #print("physical address: " + str(hex(physical_address)))
           
            
            #print("------Returning------")
            if recursion_depth == 1:
                #return hex(physical_address >> 12)
                #print( str(hex(physical_address >> 12) + hex(offset)[2:]))
                return hex(physical_address >> 12) + hex(offset)[2:]

            else:
                return hex(physical_address) + hex(offset)[2:] #offset removes the 0x, we could use zfill to ensure proper length.


        except KeyError as key_error:
            self.page_miss_cnt += 1 # Everytime we run the except it means we had a page miss

            # Page miss occurred, recursively call the function with the new virtual address
            #print("------Page Miss------")
            
            last_address = str(key_error.args[0]) #Extract argument from the KeyError
            #print("KeyError Address: " + last_address)
            
            new_cr3 = self.ept_ptr  # Use EPT_PTR as CR3
            last_address = int(last_address, 16)     
            
           
            #print(str(last_address) + " " + new_cr3)
            # Recursive call with the updated last_address

            resolved_address = self.translate_virtual_to_physical(last_address, new_cr3, recursion_depth + 1)
            #print("hypervisor address: " + str(resolved_address))
            #print(" Checking address: " + str(hex(last_address)))
            #print(" last used address: " + str(hex(current_address)))
            #print("current table level: " + str(self.current_table_level))

            #If by this point we have two page misses it means we didn't find it in the CR3 and the EPT hence a page fault has occured. 
            if (self.page_miss_cnt == 2):
                return "A Page Fault has occurred: Page not found in Guest OS Tables and Hypervisor Tables."
            
            #------Replace address with the new one------ 
            #if((self.current_table_level - 1) == 2):
                #self.ept_tables[hex(pdpt_entry)][pdpt_index] = resolved_address
                #self.ept_tables[hex(pml4_entry)][pml4_index] = resolved_address
            

            #Logic for continuing the Page walk:
            #The current_table_level will be read in order to know where to continue
            #Then we will run the code blocks to find the physical address continuing where we last left off.

            if((self.current_table_level) == 0):

                pdpt_entry = int(self.ept_tables[hex(int(resolved_address, 16))][pml4_index], 16)
                pd_entry = int(self.ept_tables[hex(pdpt_entry)][pdpt_index], 16)
                pt_entry = int(self.ept_tables[hex(pd_entry)][pd_index], 16)    
                physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
                

            if((self.current_table_level) == 1):

                pd_entry = int(self.ept_tables[hex(int(resolved_address, 16))][pdpt_index], 16)
                pt_entry = int(self.ept_tables[hex(pd_entry)][pd_index], 16)    
                physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
               

            if((self.current_table_level) == 2):

                pt_entry = int(self.ept_tables[hex(int(resolved_address, 16))][pd_index], 16)   
                print(pt_entry) 
                physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
                

            if((self.current_table_level) == 3):

                physical_address = int(self.ept_tables[hex(int(resolved_address, 16))][pt_index], 16)
               
            #pt_entry = int(self.ept_tables[hex(pd_entry)][pd_index], 16)
            #print("pt address: " + str(hex(pt_entry)))
            
            #physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
            #print("physical address: " + str(hex(physical_address)))



            


            return hex(physical_address >> 12) + hex(offset)[2:]
 
#This behavior doesn't exactly match my expectations. (Behavior for case 2) 
#I would expect us to resume from table two to find the header using our resolved address: 0x23dd279bcb2c161c
#Then using pd index 88 to find the third address then using this one with the pt index 227 to find the last physical address.
#Though oddly in the CSV the resolved address is basically the last table almost as if we were skipping the 3rd table, 
#Since at the moment the address: 0x74cdb6a25971a000 is found inside the 0x23dd279bcb2c161c table
#Either way if this behavior needed to be changed its mostly just needing to do a change to how we handle the if statements above
#Adding more entries to suit the expected behavior and changing the current_table_levels.

#I discussed this with a fellow student, just in case and we both came to similar conclusions.
#Here is a link with a visualization of what is somewhat going on.
# https://docs.google.com/presentation/d/1CG9wjQz7Y9K65RhKudFksJg0h9xSwVX1spDeB4wP3Vw/edit?usp=sharing

#I assume I might be somewhat confusing something so I might need some guidance in case.







#Had to change format due to moodle errors relating to sys.argv length?

def main(): 
    cr3_register = sys.argv[1]
    ept_ptr = sys.argv[2]
    ept_tables_file = sys.argv[3]
    virtual_address = sys.argv[4]

    page_walk = PageWalk(cr3_register, ept_ptr, ept_tables_file)
    physical_address = page_walk.translate_virtual_to_physical(int(virtual_address, 16))

    print(str(physical_address))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()



            # if((self.current_table_level - 1) == 0):

            #     pdpt_entry = int(self.ept_tables[hex(int(resolved_address, 16))][pml4_index], 16)
            #     pd_entry = int(self.ept_tables[hex(pdpt_entry)][pdpt_index], 16)
            #     pt_entry = int(self.ept_tables[hex(pd_entry)][pd_index], 16)    
            #     physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
                

            # if((self.current_table_level - 1) == 1):

            #     pd_entry = int(self.ept_tables[hex(int(resolved_address, 16))][pdpt_index], 16)
            #     pt_entry = int(self.ept_tables[hex(pd_entry)][pd_index], 16)    
            #     physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
               

            # if((self.current_table_level - 1) == 2):

            #     pt_entry = int(self.ept_tables[hex(int(resolved_address, 16))][pd_index], 16)   
            #     print(pt_entry) 
            #     physical_address = int(self.ept_tables[hex(pt_entry)][pt_index], 16)
                

            # if((self.current_table_level - 1) == 3):

            #     physical_address = int(self.ept_tables[hex(int(resolved_address, 16))][pt_index], 16)