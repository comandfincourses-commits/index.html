import sys
from PIL import Image, ImageDraw, ImageFont
out, title, part, nxt = sys.argv[1:5]
W,H=1080,1920
B="/usr/share/fonts/opentype/inter/Inter-Black.otf"; SB="/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
SER="/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
GOLD=(214,170,84); NAVY=(13,27,52); GREEN=(22,170,120)
def ctr(d,y,t,f,fill):
    w=d.textlength(t,font=f); d.text(((W-w)/2,y),t,font=f,fill=fill)
# 1) persistent overlay for the story section
im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
ctr(d,330,title.upper(),ImageFont.truetype(SER,92),GOLD)
f=ImageFont.truetype(SB,40); t=f"PART {part}"; w=d.textlength(t,font=f)
d.rounded_rectangle(((W-w)/2-28,450,(W+w)/2+28,512),12,fill=NAVY); d.text(((W-w)/2,458),t,font=f,fill="white")
ctr(d,1440,"Follow for the next part",ImageFont.truetype(SB,44),"white")
ctr(d,1510,"@COMandFIN",ImageFont.truetype(B,52),GOLD)
im.save(out+"_story.png")
# 2) end-card overlay
im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
ctr(d,250,f"PART {nxt}",ImageFont.truetype(B,120),GOLD)
ctr(d,400,"COMING NEXT",ImageFont.truetype(SB,60),"white")
for i,(t,c) in enumerate([("FOLLOW",GREEN),("SUBSCRIBE",(200,30,30))]):
    f=ImageFont.truetype(B,64); w=d.textlength(t,font=f); y=1380+i*130
    d.rounded_rectangle(((W-w)/2-50,y,(W+w)/2+50,y+100),50,fill=c); d.text(((W-w)/2,y+12),t,font=f,fill="white")
ctr(d,1660,"for all parts of the series",ImageFont.truetype(SB,42),"white")
im.save(out+"_end.png")
