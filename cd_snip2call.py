''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.7.2 2018-02-08'
ToDo: (see end of file)
'''

import  re, os, json, itertools, collections
from    fnmatch         import fnmatch
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    .cd_plug_lib    import *

OrdDict = collections.OrderedDict

# I18N
_       = get_translation(__file__)

pass;                           LOG     = (-1== 1)  # Do or dont logging.

co_sgns     = [sgn                      for sgn in dir(cmds) if sgn.startswith('cCommand_') 
                                                             or sgn.startswith('cmd_')]
CO_SGN2CID  = {sgn:eval('cmds.'+sgn)    for sgn in co_sgns}
CO_CID2SGN  = {cid:sgn                  for sgn,cid in CO_SGN2CID.items()}

snip2call_json= app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_snip2call.json'
class SnipData:
    """ SnipData.is_snip(text)  # Test
        sd = SnipData()         # Load snips, prepare fields
        sd.cmd_ids()            # Iterate all core/plug cmd-ids
        sd.get_name(cid)        # 
        sd.get_snips(cid)->list # All snips for cmd-id
        sd.get_cmdid(snip)      # 0/1 cmd-id for snip
        sd.set(snip, cid)       # Assign snip to cmd-id. Old snip-assigning will be removed
    """

#   msg_correct_snip    = _('Permitted character in snip: letters')
    msg_correct_snip    = _('Snip characters: letters, digits, "_". First character must be letter.')
    snip_help           = _('''
"Snip" is an alternative way to call commands.
    
• Simple case:
    "pu" is snip for command PageUp.
    Type in any text
        /pu
    and press Tab-key.
    Fragment "/pu" will be removed from text and undo-history, 
    command PageUp will be called.
• More complex case:
    Type
        /3pu
    and command will be called 3 times.
    
Snip contains only letters, digits, "_", and starts with a letter.
        
Any command can have many snips assigned to it.
It's a good idea to assign keystrokes, for all available keyboard layouts, to the same command.
                        ''').strip()
    @staticmethod
    def is_snip(text):
        return  text.isidentifier() and text[0].isalpha()
    
    STARTC  = '/'               # Char to begin snip in line
    PAPAMC  = '.'               # Char to begin param-substring in snip
    reRpSnPr= re.compile(f(r'(?P<rp>\d*)'       # Repeater digits (opt)
                           r'(?P<sn>[^{}]+)'    # Snip
                           r'{}?'               # 
                           r'(?P<pr>.*)'        # Param (opt)
                          ,PAPAMC, PAPAMC)
                        )
    @staticmethod
    def parse_snip_env(rp_snp_pr):
        mgRpSnPr= SnipData.reRpSnPr.match(rp_snp_pr).groupdict()
        rpt     = mgRpSnPr['rp']
        snp     = mgRpSnPr['sn']
        prm     = mgRpSnPr['pr']
        return  rpt,snp,prm

    CID2NMS = None              # {cid:nm} for core/plug

    @staticmethod
    def get_name(cid):
        return SnipData.CID2NMS.get(CO_SGN2CID.get(cid, cid))
    
    def __init__(self):
        pass;                  #LOG and log('ok',())
        self.snip_js    = json.loads(open(    snip2call_json).read()) \
                            if os.path.exists(snip2call_json) else \
                          {}
        self.snp2csgn   = self.snip_js.setdefault('snip2cid', {})
        self.snp2cid    = None  # {snp:<int cid|plug-id>}
        self.cid2snps   = None  # {cid:[snip]}
        self._prepare()
    def _prepare(self):
        """ Update members for new state of self.snp2csgn """
        self.snp2cid    = {snp:CO_SGN2CID.get(csgn, csgn) for snp,csgn in self.snp2csgn.items()}
        self.cid2snps   = {cid:[] for cid in self.snp2cid.values()}
        for snp,cid in self.snp2cid.items():
            self.cid2snps[cid] += [snp]
       #def _prepare
    
    def free(self, snp):
        self.snp2csgn.pop(snp, None)
        open(snip2call_json, 'w').write(json.dumps(self.snip_js, indent=4))
        self._prepare()
        
    def set(self, snp, cid):
        # Assign snip to cmd-id. Old snip-assigning will be removed
        self.snp2csgn[snp] = CO_CID2SGN.get(cid, cid)
        open(snip2call_json, 'w').write(json.dumps(self.snip_js, indent=4))
        self._prepare()
    
    def cmd_ids(self):
        # List of cmd-ids
        return list(SnipData.CID2NMS.keys())
        
    def get_snips(self, cid)->list:
        # All snips for cmd-id
        return self.cid2snps.get(CO_SGN2CID.get(cid, cid), ())
    def get_cmdid(self, snp, defval=None):
        # cmd-id for snip
        return self.snp2cid.get(snp, defval)

    @staticmethod
    def _load_CID2NMS():
        cid2nms = OrdDict()
        if True: #app.app_api_version()>='1.0.212':
            lcmds   = app.app_proc(app.PROC_GET_COMMANDS, '')
            for cmd in lcmds:
                if cmd['type'] not in ('cmd', 'plugin'): continue
                cid2nms[cmd['cmd'] 
                            if cmd['type']=='cmd' else 
                        f('{},{},{}', cmd['p_module'], cmd['p_method'], cmd['p_method_params']).rstrip(',')
                       ]    = cmd['name']
#       else: # old version
#           # Core cmds
#           for n in itertools.count():
#               if not    app.app_proc(app.PROC_GET_COMMAND, str(n)): break#for n
#               cid,cnm,\
#               ck1,ck2 = app.app_proc(app.PROC_GET_COMMAND, str(n))
#               if cid<=0:                      continue#for n
#               if cnm.endswith(r'\-'):         continue#for n      # command for separator in menu
#               if cnm.startswith('lexer:'):    continue#for n      # ?? lexer? smth-more?
#               if cnm.startswith('plugin:'):   continue#for n      # ?? plugin? smth-more?
#               cid2nms[cid]    = cnm
#              #for n
#           pass;               #LOG and log('|cid2nms|={}',len(cid2nms))
#           pass;               #LOG and log('|CO_CID2SGN|={}',len(CO_CID2SGN))
#           pass;               #LOG and log('diff={}',({cid for cid in cid2nms}-{cid for cid in CO_CID2SGN}))
#           pass;               #LOG and log('diff={}',({cid for cid in CO_CID2SGN}-{cid for cid in cid2nms}))
#           pass;               #LOG and log('diff={}',({cid:sgn  for cid,sgn in CO_CID2SGN.items() if cid not in cid2nms}))
#           pass;               #assert {cid for cid in cid2nms}=={cid for cid in CO_CID2SGN}    
#           for n in itertools.count():
#               if not    app.app_proc(app.PROC_GET_COMMAND_PLUGIN, str(n)): break#for n
#               pnm,    \
#               modul,  \
#               meth,   \
#               par,    \
#               lxrs    = app.app_proc(app.PROC_GET_COMMAND_PLUGIN, str(n))
#               if pnm.endswith(r'\-'):         continue#for n      # command for separator in menu
#               pid     = modul+','+meth+(','+par if par else '')
#               cid2nms[pid]    = 'plugin: '+pnm.replace('&', '').replace('\\', ': ')
#              #for n
        return cid2nms
       #def _load_CID2NMS

   #class SnipData
SnipData.CID2NMS = SnipData._load_CID2NMS()

class Command:
    def __init__(self):
        self.sndt   = SnipData()
        pass;                  #LOG and log('ok',())
    
    def dlg(self):
        if app.app_api_version()<'1.0.212':     # depr PROC_GET_COMMAND, PROC_GET_COMMAND_PLUGIN
            return app.msg_status(_('Need update CudaText'))
        sndt    = self.sndt
        reND    = re.compile(r'\W')
        def is_cond4name(cond, text):
            if not cond:    return True
            if '_' in cond:
                text    = '·' + reND.sub('·', text) + '·'
                cond   = ' ' + cond + ' '
                cond   = cond.replace(' _', ' ·').replace('_ ', '· ')
            pass;                  #LOG and log('cond, text={}',(cond, text))
            return all(map(lambda cw: cw in text, cond.split()))
        def is_cond4snps(cond, sns_l):
            if not cond:    return  True
            if not sns_l:   return  False
            return any(map(lambda sn:fnmatch(sn, cond), sns_l))
        def bmix(val1, bor2, val2):
            return val1 or val2     if bor2 else        val1 and val2
        cmds_l  = [(cid, sndt.get_name(cid)) for cid in sndt.cmd_ids()]
        
        ccnd_h      = _('Suitable command names will contain all specified words.'
                      '\r · Case is ignored.'
                      '\r · Use "_" for word boundary.'
                      '\r     "_up" selects "upper" but not "group".')
        scnd_h      = _('Suitable command snips will match specified string.'
                      '\r · Case is important.'
                      '\r · Use ? for any character and * for any fragment.')
        
        cmd_id      = ''
        ccnd        = ''
        scnd        = ''
        orcn        = False
        focused     = 'ccnd'
        while True:
            pass;              #LOG and log('ccnd, scnd={}',(ccnd, scnd))
            cins_l  = [    (cid, cnm, sndt.get_snips(cid)) 
                        for cid, cnm in cmds_l]
            fcins_l = [    (cid, cnm, sns)
                       for (cid, cnm, sns)   in cins_l
                       if  bmix(        not ccnd or is_cond4name(ccnd.upper(), cnm.upper())
                               ,orcn,   not scnd or is_cond4snps(scnd, sns)
                               ) ]
            fi_l    = [     cid
                       for (cid, cnm,  sn) in fcins_l]
            stat    = f(' ({}/{})',len(fcins_l), len(cmds_l))
            itms    = (zip([_('Command')+stat, _('Snip(s)')], map(str, [350, 150]))
                      ,    [ (cnm,                ', '.join(sns)) 
                            for  (cid, cnm, sns) in fcins_l ])
            cnts    =[dict(cid='fltr',tp='bt'  ,tid='scnd'  ,l=5+520+5  ,w=110  ,cap=_('&Filter')       ,props='1'          ) # &f  default
                     ,dict(cid='drop',tp='bt'  ,t=5+50      ,l=5+520+5  ,w=110  ,cap=_('&All')                              ) # &a
                     ,dict(cid='orcn',tp='ch'  ,t=5         ,l=5+300    ,w=40   ,cap=_('&OR')           ,act='1'            ) # &o
                     ,dict(           tp='lb'  ,tid='orcn'  ,l=5+5      ,w=90   ,cap=_('In &Command:')          ,hint=ccnd_h) # &c
                     ,dict(cid='ccnd',tp='ed'  ,t=5+20      ,l=5+5      ,w=150                                              ) #
                     ,dict(           tp='lb'  ,tid='orcn'  ,l=5+350+5  ,w=50   ,cap=_('In &Snip(s):')          ,hint=scnd_h) # &s
                     ,dict(cid='shlp',tp='bt'  ,tid='orcn'  ,l=5+350+5+80,w=20   ,cap=_('&?')                                ) # &?
                     ,dict(cid='scnd',tp='ed'  ,t=5+20      ,l=5+350+5  ,w=100                                              ) #
                     ,dict(cid='lwcs',tp='lvw' ,t=5+50      ,l=5        ,w=520,h=535  ,items=itms       ,props='1'          ) #     grid
                     ,dict(cid='asnp',tp='bt'  ,t=200       ,l=5+520+5  ,w=110  ,cap=_('A&dd Snip')                         ) # &d
                     ,dict(cid='rsnp',tp='bt'  ,t=200+30    ,l=5+520+5  ,w=110  ,cap=_('F&ree Snip(s)')                     ) # &r
                     ,dict(cid='help',tp='bt'  ,t=600-65    ,l=5+520+5  ,w=110  ,cap=_('Hel&p')                             ) # &p 
                     ,dict(cid='-'   ,tp='bt'  ,t=600-35    ,l=5+520+5  ,w=110  ,cap=_('Close')                             ) #  
                    ]
            lwcs_n  = -1    if 0==len(fi_l)          else \
                       0    if cmd_id not in fi_l    else \
                       fi_l.index(cmd_id)
            pass;              #    LOG and log('stat, lwcs_n={}',(stat, lwcs_n))
            vals    =       dict(ccnd=ccnd
                                ,scnd=scnd
                                ,orcn=orcn
                                ,lwcs=lwcs_n)
            pass;                  #LOG and log('in-vals={}',(vals))
            btn, vals, chds = dlg_wrapper(_('Configure "SnipToCall"'), 650-5, 600, cnts, vals, focus_cid=focused)
            pass;                  #LOG and log('an-vals={}',(vals))
            pass;                  #LOG and log('chds={}',(chds))
            if btn is None or btn=='-':    return#while True
            focused = chds[0] if 1==len(chds) else focused
            ccnd    = vals['ccnd'].strip()
            scnd    = vals['scnd'].strip()
            orcn    = vals['orcn']
            lwcs_n  = vals['lwcs']
            cmd_id  = '' if lwcs_n==-1 else fi_l[lwcs_n]
            if False:pass
            elif btn in 'fltr':
                focused = 'lwcs'
            elif btn=='drop':
                ccnd    = ''
                scnd    = ''
                focused = 'ccnd'

            elif btn=='shlp':
                app.msg_box(sndt.snip_help, app.MB_OK)
            elif btn=='help':
                dlg_wrapper(_('Help for "Config SnipToCall"'), 410, 310,
                     [dict(cid='htxt',tp='me'    ,t=5  ,h=300-28,l=5          ,w=400  ,props='1,0,1'  ) #  ro,mono,border
                     ,dict(cid='-'   ,tp='bt'    ,t=5+300-23    ,l=5+400-80   ,w=80   ,cap=_('&Close'))
                     ], dict(htxt=f(_('• In Command.'
                                      '\r{ccnd_h}'
                                      '\r '
                                      '\r• In Snip. '
                                      '\r{scnd_h}'
                                      '\r '), ccnd_h=ccnd_h, scnd_h=scnd_h)
                     ), focus_cid='htxt')
            
            elif btn=='rsnp' and cmd_id:
                cnm     = sndt.get_name(cmd_id)
                snp_l   = sndt.get_snips(cmd_id)
                snps    = ', '.join(snp_l)
                if app.msg_box(f(_('Do you want to remove snip(s) '
                                   '\n    {}'
                                   '\nfor command "{}"?')
                                , snps, cnm), app.MB_OKCANCEL)==app.ID_CANCEL: continue#while
                for snp in snp_l:
                    sndt.free(snp)
                
            elif btn=='asnp' and cmd_id:
                cnm     = sndt.get_name(cmd_id)
                new_sn  = app.dlg_input(f(_('Add snip for "{}"'), cnm), '') 
                if not new_sn:  continue#while
                while not SnipData.is_snip(new_sn):
                    app.msg_status(SnipData.msg_correct_snip)
                    new_sn  = app.dlg_input(f(_('Snip for "{}"'), cnm), new_sn) 
                    if not new_sn:  break
                if not new_sn:  continue#while
                pre_cid = sndt.get_cmdid(new_sn)
                if pre_cid:
                    pre_cnm = sndt.get_name(pre_cid)
                    if app.msg_box(f(_('Snip "{}" is already assigned '
                                       '\nto command "{}".'
                                       '\n'
                                       '\nDo you want to reassign the snip '
                                       '\nto command "{}"?')
                                    , new_sn, pre_cnm, cnm), app.MB_OKCANCEL)==app.ID_CANCEL: continue#while
                sndt.set(new_sn, cmd_id)
           #while
       #def dlg
    
    def on_key(self, ed_self, code, state):
        if app.app_api_version()<'1.0.212':     # depr PROC_GET_COMMAND, PROC_GET_COMMAND_PLUGIN
            return app.msg_status(_('Need update CudaText'))
        pass;                  #LOG and log('code, state={}',(code, state))
        if code!=9:                     return True # tab-key=9
        if state:                       return True # SCAM
        pass;                   LOG and log('self.sndt.snp2csgn={}',(self.sndt.snp2csgn))
        if not self.sndt.snp2csgn:      return True # no snips
        if ed_self.get_prop(app.PROP_TAB_COLLECT_MARKERS): return # TAB busy
        
        crts    = ed_self.get_carets()
        if len(crts)>1:                 return True # many carets
        (cCrt, rCrt
        ,cEnd, rEnd)= crts[0]
        if -1!=cEnd or cCrt<2:          return True # with selection

        line    = ed_self.get_text_line(rCrt)
        posC    = line.rfind(SnipData.STARTC, 0, cCrt)
        pass;                   LOG and log('SnipData.STARTC={}',(SnipData.STARTC))
        pass;                   LOG and log('line, posC={}',(line, posC))
        if -1==posC or posC+1==cCrt:    return True # no sign or too near
        rp_snp_pr = line[posC+1:cCrt]
        rpt,snp,prm = SnipData.parse_snip_env(rp_snp_pr)
#       mgRpSnPr= SnipData.reRpSnPr.match(rp_snp_pr).groupdict()
#       rpt     = mgRpSnPr['rp']
#       snp     = mgRpSnPr['sn']
#       prm     = mgRpSnPr['pr']
#       posP    = rp_snp_pr.find(SnipData.PAPAMC)
#       if -1!=posP:
#           snp = line[:posP]
#           prm = line[posP+1:]
        pass;                   LOG and log('rpt,snp,prm={}',(rpt,snp,prm))

        cid     = self.sndt.get_cmdid(snp)
        if not cid:                     return True # no such snip
        pass;                  #LOG and log('cid={}',(cid))

        # Eliminate snp from text
        if not 'Simple way - cut':
            ed_self.delete(   cCrt-len(rp_snp_pr)-1, rCrt, cCrt, rCrt)
            ed_self.set_caret(cCrt-len(rp_snp_pr)-1, rCrt)
        if 'Complex way - undo':
            line_snp= line
            line_pre= line_snp
            line_pur= line_snp[:cCrt-len(rp_snp_pr)-1] + line_snp[cCrt:]
            pass;              #LOG and log('line_pur={}',(line_pur))
            pass;              #LOG and log('line_snp={}',(line_snp))
            good    = False
            undos   = 0
            for iun in range(1+len(rp_snp_pr)):
                ed_self.cmd(cmds.cCommand_Undo)
                undos  += 1
                line_und= ed_self.get_text_line(rCrt)
                pass;          #LOG and log('line_und={}',(line_und))
                if line_pre==line_pur:
                    pass;      #LOG and log('Not hot-snip',())
                    for ird in range(undos):
                        ed_self.cmd(cmds.cCommand_Redo)
                    return True # Not hot-snip
                if line_und==line_pur:
                    pass;      #LOG and log('Good hot-snip',())
                    good    = True
                    break#for iun
                line_pre= line_und
               #for iun
            if not good:
                pass;          #LOG and log('Not good',())
                for ird in range(undos):
                    ed_self.cmd(cmds.cCommand_Redo)
                return True # Not hot-snip

        self._call_cmd(ed_self, cid, rpt, prm)
        return False #block tab-key
       #def on_key
    
    def _call_cmd(self, ed_self, cid, rpt, prm):
        for rp in range(int(rpt) if rpt else 1):
            if False:pass
            elif type(cid)==int or cid.isdigit():
                # Core cmd number
                ed_self.cmd(int(cid))
            elif cid in CO_SGN2CID:
                # Core cmd name
                ed_self.cmd(CO_SGN2CID[cid])
            else:
                # Plugin cmd
                app.app_proc(app.PROC_EXEC_PLUGIN, cid)
'''
ToDo
[ ][kv-kv][16jun16] Start
[ ][kv-kv][24jun16] Many snip for one cmd
'''
