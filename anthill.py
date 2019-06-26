import ui,scene,time
import scene_drawing as scdr
from math import floor,ceil,exp,log,sqrt

def _hd(d,cap=False):
    if d<10:
        return str(d)
    elif cap:
        return chr(d-10+ord('A'))
    else:
        return chr(d-10+ord('a'))

def hsv2rgb(*hsv): # [3x ~1] in, [3x ~1] out
    h,s,v=hsv[0] if len(hsv)==1 else hsv
    hi=floor(6*h)%6
    vmin=(1-s)*v
    a=(v-vmin)*((6*h)%1)
    if hi==0:
        return(v,vmin+a,vmin)
    elif hi==1:
        return(v-a,v,vmin)
    elif hi==2:
        return(vmin,v,vmin+a)
    elif hi==3:
        return(vmin,v-a,v)
    elif hi==4:
        return(vmin+a,vmin,v)
    else:
        return(v,vmin,v-a)

def hex2rgb(hexstr): # 'abcdef' in, [3x ~1] out
    rgb=[]
    for i in range(3):
        rgb.append(int(hexstr[2*i:2*i+2],16)/255)
    return rgb

def rgb2hsv(*rgb): # [3x ~1] in, [3x ~1] out
    r,g,b=rgb[0] if len(rgb)==1 else rgb
    m=min(r,g,b)
    V=max(r,g,b)
    S=1-m/V if V else 0
    if m==V:
        return (0, 0, V)
    elif V==r:
        H=(g-b)/(V-m)
        if H<0:
            H+=6
    elif V==g:
        H=(b-r)/(V-m)+2
    else:
        H=(r-g)/(V-m)+4
    return (H/6, S, V)

def rgb2hex(*rgb): # [3x ~1] in, 'abcdef' out
    if len(rgb)==1:
        rgb=rgb[0]
    hex=''
    for i in rgb:
        el=int(round(i*255,0))
        hex+=_hd(el//16)+_hd(el%16)
    return hex

def hsv2hex(*hsv):
    if len(hsv)==1:
        hsv=hsv[0]
    return rgb2hex(hsv2rgb(hsv))

def toggleTVedit(sender):
    global v
    if v['rules'].editing:
        v['rules'].editing=False
        sender.title='Edit'
    else:
        v['rules'].editing=True
        sender.title='Done'

def newrule(sender):
    global ahtvds
    ahtvds.items.append([0,(0,0,0)])
    ah.types=ahtvds.items[1:]
    ah.typenum=len(ah.types)
    ahtvds.tv.reload_data()

def zoomset(sender):
    global v,ah
    val=int(round(exp(log(150)*sqrt(sender.value)),0))
    ah.zoom=val
    ah.ds=None
    v['zoomlab'].text=str(val)+'x'

def velset(sender):
    global v,ah
    val=int(round(exp(log(1000)*sqrt(sender.value)),0))
    ah.speed=val
    v['vellab'].text=str(val)+' Hz'

def setAHstate(state):
    global ah,v
    if state==1:
        if ah.state:
            ah.state=state
    else:
        if bool(state)!=bool(ah.state):
            for i in v['ber'],v['bnr']:
                i.enabled=not i.enabled
        ah.state=state

class AHTVDS:
    def __init__(self,tv,dg):
        self.bgactive=False
        self.tv=tv
        self.dg=dg
        self.dg.ds=self
        self.items=[[0,(1,1,1)],[1,(1,0,0)]]
        self.tv.data_source=self
    
    def tableview_number_of_sections(self, tableview):
        return 1

    def tableview_number_of_rows(self, tableview, section):
        return len(self.items)

    def tableview_cell_for_row(self, tableview, section, row):
        cell=ui.TableViewCell()
        cell.text_label.text=''
        cell.accessory_type='disclosure_indicator'
        sc=ui.SegmentedControl(name=str(row),frame=(57,4,215,29),flex='W',
            segments=['L','R','F','B'],action=self.switchdr)
        sc.selected_index=self.items[row][0]
        colour=ui.View(frame=(275,3,31,31),flex='L',
            border_width=1,background_color=self.items[row][1])
        if not row:
            cell.content_view.add_subview(ui.Switch(x=3,y=3,value=self.bgactive,action=self.switchbga))
            if not self.bgactive:
                sc.hidden=True
        for i in sc,colour:
            cell.content_view.add_subview(i)
        return cell

    def tableview_can_delete(self, tableview, section, row):
        return bool(row)

    def tableview_can_move(self, tableview, section, row):
        return bool(row)

    def tableview_delete(self, tableview, section, row):
        del self.items[row]
        ah.types=self.items[1:]
        ah.typenum=len(ah.types)
        self.tv.reload_data()

    def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
        global ah
        if not to_row:
            to_row=1
        if from_row>to_row:
            self.items=self.items[:to_row]+[self.items[from_row]]+self.items[to_row:from_row]+self.items[from_row+1:]
        elif from_row<to_row:
            self.items=self.items[:from_row]+self.items[from_row+1:to_row+1]+[self.items[from_row]]+self.items[to_row+1:]
        ah.types=self.items[1:]
        ah.typenum=len(ah.types)
        tableview.reload_data()
    
    def switchbga(self,sender):
        global ah
        self.bgactive=sender.value
        ah.bga=sender.value
        self.tv.reload_data()
    
    def switchdr(self,sender):
        global ah
        i=int(sender.name)
        val=sender.selected_index
        self.items[i][0]=val
        '''if i:
            ah.types[i-1][0]=val
        else:
            ah.bgr[0]=val'''
        self.tv.reload_data()

class AHTVDG:
    def __init__(self,tv):
        self.ds=None
        tv.delegate=self
    
    def tableview_did_select(self, tableview, section, row):
        global v
        v['cpk'].load(self.ds,row)
        tableview.selected_row=(0,-1)

class ColourPicker(ui.View):
    def __init__(self,width=340,height=180):
        self.ds=None
        self.dsrow=None
        self.width=width
        self.height=height
        self.add_subview(ui.Button(name='bb',frame=(0,0,72,32),
            title='Back',image=ui.Image.named('iob:ios7_arrow_back_24'),action=self.unload))
        self.add_subview(ui.Label(name='lt',center=(self.width//2,16),flex='LR',
            text='',font=('<system>',19),alignment=1))
        self.add_subview(ui.SegmentedControl(name='sc',frame=(0,42,232,30),segments=['RGB','HSV'],
            selected_index=0,action=self.upd))
        self.add_subview(ui.TextField(name='thex',frame=(238,40,102,30),action=self.upd))
        for i in range(3):
            self.add_subview(ui.Slider(name='s'+str(i),frame=(0,78+34*i,196,34),continuous=True,
                action=self.upd,value=1))
            self.add_subview(ui.TextField(name='t'+str(i),frame=(196,78+34*i,42,34),font=('<system>',14),
                action=self.upd,value=1))
        self.add_subview(ui.View(name='res',frame=(238,78,102,102)))
    
    def did_load(self):
        self.background_color='#ffffff'
        self.upd()
    
    def load(self,ds,row):
        self.ds=ds
        self.dsrow=row
        self['lt'].text='Type '+str(row)
        self['thex'].text=rgb2hex(ds.items[row][1])
        self.upd(self['thex'])
        self.hidden=False
    
    def unload(self,sender):
        global ah
        res=[self['s'+str(i)].value for i in range(3)]
        if self['sc'].selected_index:
            res=hsv2rgb(res)
        self.ds.items[self.dsrow][1]=tuple(res)
        self.ds.tv.reload_data()
        ah.upd(dstate=3)
        self.hidden=True
    
    def upd(self,sender=None):
        muls=((255,255,255),(360,100,100))
        colour=None
        mind=self['sc'].selected_index
        if sender==None:
            for i in range(3):
                self['t'+str(i)].text=str(int(round(muls[mind][i]*self['s'+str(i)].value,0)))
                colour='ffffff'
        elif sender.name=='sc':
            res=[self['s'+str(i)].value for i in range(3)]
            newres=rgb2hsv(res) if mind else hsv2rgb(res)
            for i in range(3):
                v,m=newres[i],muls[mind][i]
                self['s'+str(i)].value=v
                self['t'+str(i)].text=str(int(round(v*m,0)))
        elif sender.name=='thex':
            colour=sender.text
            res=hex2rgb(colour)
            if mind:
                res=rgb2hsv(res)
            for i in range(3):
                v,m=res[i],muls[mind][i]
                self['s'+str(i)].value=v
                self['t'+str(i)].text=str(int(round(v*m,0)))
        else:
            if sender.name[0]=='s':
                self['t'+sender.name[1]].text=str(int(round(muls[mind][int(sender.name[1])]*sender.value,
                    0)))
            else:
                self['s'+sender.name[1]].value=float(sender.text)/muls[mind][int(sender.name[1])]
            res=[self['s'+str(i)].value for i in range(3)]
            colour=hsv2hex(res) if mind else rgb2hex(res)
        if colour:
            self['thex'].text=colour
            self['res'].background_color='#'+colour

class Anthill(scene.Scene):
    def setup(self):
        self.state=3
        self.zoom=150
        self.ds=None
        self.speed=1
        self.pts=0
        self.antpos=[0,0]
        self.antdir=0
        self.bga=False
        self.bgr=[2,(1,1,1)]
        self.types=[]
        self.typenum=0
        self.content=dict()
        self.background_color='white'
        self.redraw=[]
    
    def upd(self,**kwarg):
        for i in kwarg:
            if i in dir(self):
                self.__setattr__(i,kwarg[i])
            elif i=='dstate':
                self.state+=kwarg[i]
    
    def draw(self):
        if self.ds:
            dn,dx=self.ds
            z=self.zoom
            if True:
                for x in range(-dn,dn+1):
                    for y in range(-dn,dn+1):
                        if (x,y) in self.content:
                            t=self.content[x,y]
                            scdr.fill(self.types[t][1])
                        else:
                            scdr.fill(self.bgr[1])
                        xr=dx+z*(dn+x)
                        yr=dx+z*(dn+y)
                        scdr.rect(xr,yr,z,z)
            elif self.redraw:
                x,y=self.redraw
                if (x,y) in self.content:
                    t=self.content[x,y]
                    scdr.fill(self.types[t][1])
                else:
                    scdr.fill(self.bgr[1])
                xr=dx+z*(dn+x)
                yr=dx+z*(dn+y)
                scdr.rect(xr,yr,z,z)
            #self.redraw=None
    
    def onestep(self):
        # TURN, JUMP, PAINT
        rs=[3,1,0,2]
        ap=tuple(self.antpos)
        if ap in self.content:
            r=self.types[self.content[ap]][0]
            self.antdir=(self.antdir+rs[r])%4
        elif self.bga:
            r=self.bgr[0]
            self.antdir=(self.antdir+rs[r])%4
        dr=self.antdir
        if dr==0:
            self.antpos[1]+=1
        elif dr==1:
            self.antpos[0]+=1
        elif dr==2:
            self.antpos[1]-=1
        else:
            self.antpos[0]-=1
        ap=tuple(self.antpos)
        if ap in self.content:
            nt=self.content[ap]+1
            if nt>=self.typenum:
                if self.bga:
                    del self.content[ap]
                else:
                    self.content[ap]=0
            else:
                self.content[ap]=nt
        else:
            self.content[ap]=0
        self.redraw=ap
    
    def update(self):
        if not self.ds:
            z=self.zoom
            dn=ceil((335-z//2)/z)
            self.ds=(dn,335-z//2-z*dn)
            self.redraw='all'
            #print(self.ds)
        if self.state<0: # STEP COMMAND RECIEVED
            self.state=1
            self.onestep()
            self.drawf()
            #print(self.content)
            #for i in ['zoom','rect','speed','bga','bgr','types','typenum']:#
                #print(i,self.__getattribute__(i))#
            return None
        elif self.state>2: # UPDATE TYPES
            self.state-=3
            global ahtvds
            self.bga=ahtvds.bgactive
            self.bgr=ahtvds.items[0]
            self.types=ahtvds.items[1:]
            self.typenum=len(self.types)
            self.redraw='all'
            return None
        if self.state==2: # RUN STATE
            t=time.time()
            if self.speed==1000:
                for i in range(1000//60+1):
                    self.onestep()
                self.draw()
            if (t-self.pts)>(1/self.speed):
                self.onestep()
                self.draw()
                self.pts=t
        #elif self.state==1: # PAUSE STATE
            #pass
        elif self.state==0: # RESET STATE
            self.content=dict()
            self.antpos=[0,0]
            self.antdir=0
            
v = ui.load_view()
ahtvdg=AHTVDG(v['rules'])
ahtvds=AHTVDS(v['rules'],ahtvdg)
ah=v['anthill'].scene
v.present('landscape')
