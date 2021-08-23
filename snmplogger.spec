# -*- mode: python -*-

# This file has been used on my win7 VM to produce the exe file.
import PyInstaller.utils.hooks
hiddenimports = ['pysnmp.smi.exval','pysnmp.cache']
block_cipher = None

x=Tree('C:\\Users\\Arqiva\\AppData\\Local\\Programs\\Python\\Python38\\Lib\\site-packages\\pysnmp\\smi\\mibs' ,prefix='pysnmp/smi/mibs')
a = Analysis(['snmp_logger_v0.4.1.py'],
             pathex=['C:\\Users\\Arqiva\\Documents\\GitHub\\SNMPmonitor\\'],
             binaries=[],
             datas=[],
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=['numpy', 'pandas'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          x,
          icon=[],
          name='snmpmonitor',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
		  upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
