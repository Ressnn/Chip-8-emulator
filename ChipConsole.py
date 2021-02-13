import numpy as np
import cv2
import keyboard



class Console():
    
    fontset = np.array([
  0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
  0x20, 0x60, 0x20, 0x20, 0x70, # 1
  0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
  0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
  0x90, 0x90, 0xF0, 0x10, 0x10, # 4
  0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
  0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
  0xF0, 0x10, 0x20, 0x40, 0x40, # 7
  0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
  0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
  0xF0, 0x90, 0xF0, 0x90, 0x90, # A
  0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
  0xF0, 0x80, 0x80, 0x80, 0xF0, # C
  0xE0, 0x90, 0x90, 0x90, 0xE0, # D
  0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
  0xF0, 0x80, 0xF0, 0x80, 0x80  # F
  ],dtype=np.uint16);
    
    
    def __init__(self,inputs=16):
        self.opcode = np.uint16(0)
        self.memory = np.zeros((4096),dtype=np.uint16)
        self.registers = np.array([np.uint8(0) for i in range(0,16)])
        
        self.memory[80:160] = self.fontset
        
        self.I = np.uint16(0)
        self.pc = np.uint16(0x200)
        
        self.HEIGHT = 32
        self.WIDTH = 64
        
        self.display = np.zeros(shape=(self.WIDTH,self.HEIGHT))
        
        self.delay_timer = np.uint16()
        self.sound_timer = np.uint16()
        
        self.stack = np.zeros((16),dtype=np.uint16)
        self.sp = np.uint8(0)
        
        self.keyboard = np.zeros(shape=inputs)
        self.window = cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        
        
        
    def load_game(self,fp):
        program = []
        with open(fp,"rb") as file:
            program += file.read(1)
            byte = program[-1]
            
            while byte != b"":
                byte = file.read(1)
                program += byte
        self.memory[512:512+len(program)] = np.array(program)

    def fetch_opcode(self,location=None):
        location = self.pc if not(location) else location
        return self.memory[location] << 8 | self.memory[location+1]
    
    def one_cycle(self):
        self.opcode = self.fetch_opcode(self.pc)
        
        self.excecute_opcode(self.opcode)
        
        self.timer_updates()      
        self.update_keyboard()
    
    @staticmethod
    def bitLen(value): 	# Gives the length of an unsigned value in bits
    	length = 0
    	while (value):
    		value >>= 1
    		length += 1
    	return(length)
    
    
    def getMSB(self,value, size):
    	length = self.bitLen(value)
    	if(length == size):
    		return 1
    	else:
    		return 0
    
    def excecute_opcode(self,opcode):
        
        decoded = self.opcode & 0xF000
        
        if decoded == 0x0000:
            
            #Clear the screen
            if opcode == 0x00E0:
                self.screen = np.zeros(64*32)
                self.pc += 2
            #Return fom subroutine
            elif opcode == 0x00EE:
                self.sp += -1
                self.pc = self.stack[self.sp]
                self.pc += 2 # Do we still increment? 
            
            #Execute machine language subroutine at address NNN
            else:
                print("Unsupported Operation")
                
        elif decoded == 0x1000:
            location = opcode & 0x0FFF
            self.pc = location
            
        elif decoded == 0x2000:
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = opcode & 0x0FFF
        
        elif decoded == 0x3000:
            register_num = (opcode & 0x0F00) >> 8
            if self.registers[register_num] == (opcode & 0x00FF):
                self.pc += 4
            else:
                self.pc += 2
            
        elif decoded == 0x4000:
            register_num = (opcode & 0x0F00) >> 8
            if self.registers[register_num] != (opcode & 0x00FF):
                self.pc += 4
            else:
                self.pc += 2
        elif decoded == 0x5000:
            register_num_x = (opcode & 0x0F00) >> 8
            register_num_y = (opcode & 0x00F0) >> 4
            
            if self.registers[register_num_x] == self.registers[register_num_y]:
                self.pc += 4
            else:
                self.pc += 2
            
        elif decoded == 0x6000:
            store_num = (opcode & 0x00FF)
            register_num_x = (opcode & 0x0F00) >> 8
            self.registers[register_num_x] = store_num
            self.pc += 2
        elif decoded == 0x7000:
            store_num = (opcode & 0x00FF)
            register_num_x = (opcode & 0x0F00) >> 8
            self.registers[register_num_x] += store_num
            self.pc += 2
        elif decoded == 0x8000:
            operation = (opcode & 0x000F) 
            
            register_num_x = (opcode & 0x0F00) >> 8 
            register_num_y = (opcode & 0x00F0) >> 4
            
            if operation == 0:
                self.registers[register_num_x] = self.registers[register_num_y]
                
            if operation == 1:
                v_x = self.registers[register_num_x]
                v_y = self.registers[register_num_y]
                
                self.registers[register_num_x] = v_x | v_y
            
            if operation == 2:
                v_x = self.registers[register_num_x]
                v_y = self.registers[register_num_y]
                
                self.registers[register_num_x] = v_x & v_y
            
            if operation == 3:
                v_x = self.registers[register_num_x]
                v_y = self.registers[register_num_y]
                
                self.registers[register_num_x] = v_x ^ v_y
            
            if operation == 4:
                v_x = self.registers[register_num_x]
                v_y = self.registers[register_num_y]
                temp = np.int32(v_x) + np.int32(v_y)
                if  temp > 255:
                    self.registers[register_num_x] = temp-256
                    self.registers[-1] = 1
                else:
                    self.registers[register_num_x] = temp
                    self.registers[-1] = 0
            
            if operation == 5:
                v_x = self.registers[register_num_x]
                v_y = self.registers[register_num_y]
                temp = np.int32(v_x) - np.int32(v_y)
                if  temp<0:
                    self.registers[register_num_x] = temp+256
                    self.registers[-1] = 0
                else:
                    self.registers[register_num_x] = temp
                    self.registers[-1] = 1
            if operation == 6:
                print("Shift")
                first = self.registers[register_num_y] & 0x1
                self.registers[register_num_x] = first >> 1
                self.registers[-1] = 1
            
            if operation == 7:
                
                if self.registers[register_num_y] > self.registers[register_num_x]:
                    self.registers[register_num_x] = self.registers[register_num_y] - self.registers[register_num_x]
                    self.registers[-1] = 1
                else:
                    self.registers[register_num_x] = 256 + self.registers[register_num_y] -self.registers[register_num_x]
                    self.registers[-1] = 0
                self.registers[register_num_x] = self.registers[register_num_x]
            
            if operation == 14:
                print("Shift")
                self.registers[0xF] = self.getMSB(self.registers[register_num_x], 8)
                self.registers[register_num_y] = (self.registers[register_num_x] << 1)
            
            self.pc+=2
        elif decoded == 0x9000:
            register_num_x = (opcode & 0x0F00) >> 8 
            register_num_y = (opcode & 0x00F0) >> 4
            
            if self.registers[register_num_x] != self.registers[register_num_y]:
                 self.pc += 4
            else:
                self.pc += 2
        
        elif decoded == 0xA000:
            self.I = opcode & 0x0FFF
            self.pc += 2
        elif decoded == 0xB000:
            self.pc = self.I + (self.opcode & 0x0FFF)
        elif decoded == 0xC000:
            value = opcode & 0x00FF
            target = (opcode & 0x0F00) >> 8
            self.registers[target] = value & np.random.randint(0, 255)
            self.pc += 2
        elif decoded == 0xD000:
            #Couldn't find original source for this peice of code but I believe I got this drawing section from stackoverflow
            x_source = (opcode & 0x0F00) >> 8
            y_source = (opcode & 0x00F0) >> 4
            x_pos = self.registers[x_source]
            y_pos = self.registers[y_source]
            num_bytes = opcode & 0x000F
            self.registers[0xF] = 0
        
            for y_index in range(num_bytes):
                color_byte = bin(self.memory[self.I + y_index])
                color_byte = color_byte[2:].zfill(8)
                y_coord = y_pos + y_index
                y_coord = y_coord % self.HEIGHT
    
                for x_index in range(8):
    
                    x_coord = x_pos + x_index
                    x_coord = x_coord % self.WIDTH
    
                    color = int(color_byte[x_index])
                    current_color = self.display[x_coord, y_coord]
    
                    if color == 1 and current_color == 1:
                        self.registers[-1] = self.registers[-1] | 1
                        color = 0
    
                    elif color == 0 and current_color == 1:
                        color = 1
    
                    self.display[x_coord, y_coord] = color
            cv2.imshow('image',self.display.T)
            cv2.waitKey(10)
            self.pc += 2
        elif decoded == 0xE000:
            if (opcode & 0x00FF) == 0x009E:
                if self.keyboard[(opcode &0x0F00) >> 8] == 1:
                    self.pc += 2
                else:
                    pass
                    
            if (opcode & 0x00FF) == 0x00A1:
                if self.keyboard[(opcode &0x0F00) >> 8] == 0:
                    #print(self.keyboard[0:10])
                    self.pc += 2
                else:
                    pass
            self.pc += 2
        elif decoded == 0xF000:
            if (opcode & 0x00FF) == 0x0007:
                self.registers[(opcode & 0x0F00) >> 8] = self.delay_timer
            
            if (opcode & 0x00FF) == 0x000A:
                target = (opcode & 0x0F00) >> 8
                while not((self.keyboard == 1).any()):
                    self.update_keyboard()
            
            if (opcode & 0x00FF) == 0x0015:
                 self.delay_timer = self.registers[(opcode & 0x0F00) >> 8]
            
            if (opcode & 0x00FF) == 0x0018:
                 self.sound_timer = self.registers[(opcode & 0x0F00) >> 8]
            
            if (opcode & 0x00FF) == 0x001E:
                 self.I += (opcode & 0x0F00) >> 8
            
            if (opcode & 0x00FF) == 0x0029:
                location = ((opcode & 0x0F00) >> 8)*5
                self.I = location
                
            if (opcode & 0x00FF) == 0x0033:
                bcd_value = '{:03d}'.format(self.registers[(opcode & 0x0F00) >> 8])
                self.memory[self.I] = int(bcd_value[0])
                self.memory[self.I + 1] = int(bcd_value[1])
                self.memory[self.I + 2] = int(bcd_value[2])
 
            if (opcode & 0x00FF) == 0x0055:
                source = (opcode & 0x0F00) >> 8
                for counter in range(source + 1):
                    self.memory[self.I + counter] = self.registers[counter]
            
            if (opcode & 0x00FF) == 0x0065:
                source = (opcode & 0x0F00) >> 8
                for counter in range(source + 1):
                    self.registers[counter] = self.memory[self.I + counter]
            
            self.pc += 2
        
    
    def timer_updates(self):
        if self.delay_timer > 0:
            self.delay_timer += -1
        if self.sound_timer > 0:
            self.delay_timer += -1
    
    def update_keyboard(self):
        keybinds = {
        "1":0,
        "2":0x1,
        "3":0x2,
        "4":0xC,
        
        "Q":0x3,
        "W":0x4,
        "E":0x5,
        "R":0xD,
            
        "A":0x6,
        "S":0x7,
        "D":0x8,
        "F":0xE,
        
        "Z":0x9,
        "X":0xA,
        "C":0xB,
        "V":0xF,}
        
        for key in keybinds:
            value = keybinds[key]
            if keyboard.is_pressed(key):
#                print("keypress")
                self.keyboard[value] = 1
            else:
                self.keyboard[value] = 0
        
if __name__ == "__main__":
    C = Console()
    C.load_game(r"Games\TETRIS")
    for i in range(0,30000):
        C.one_cycle()