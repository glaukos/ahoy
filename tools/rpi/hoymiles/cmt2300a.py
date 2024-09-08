import spidev
from enum import Enum
import RPi.GPIO as GPIO
import time

class RegionCfg(Enum):
    EUROPE = 0
    USA = 1
    BRAZIL = 2

class CmtStatus(Enum):
    SUCCESS = 0,
    ERR_SWITCH_STATE = 1
    ERR_TX_PENDING = 2
    FIFO_EMPTY = 3
    ERR_RX_IN_FIFO = 4

cmtConfig = [
            # 0x00 - 0x0f -- RSSI offset +- 0 and 13dBm
            0x00, 0x66, 0xEC, 0x1C, 0x70, 0x80, 0x14, 0x08,
            0x11, 0x02, 0x02, 0x00, 0xAE, 0xE0, 0x35, 0x00,
            # 0x10 - 0x1f
            0x00, 0xF4, 0x10, 0xE2, 0x42, 0x20, 0x0C, 0x81,
            0x42, 0x32, 0xCF, 0x82, 0x42, 0x27, 0x76, 0x12, # 860MHz as default
            # 0x20 - 0x2f
            0xA6, 0xC9, 0x20, 0x20, 0xD2, 0x35, 0x0C, 0x0A,
            0x9F, 0x4B, 0x29, 0x29, 0xC0, 0x14, 0x05, 0x53,
            # 0x30 - 0x3f
            0x10, 0x00, 0xB4, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x12, 0x1E, 0x00, 0xAA, 0x06, 0x00, 0x00, 0x00,
            # 0x40 - 0x4f
            0x00, 0x48, 0x5A, 0x48, 0x4D, 0x01, 0x1F, 0x00,
            0x00, 0x00, 0x00, 0x00, 0xC3, 0x00, 0x00, 0x60,
            # 0x50 - 0x5f
            0xFF, 0x00, 0x00, 0x1F, 0x10, 0x70, 0x4D, 0x06,
            0x00, 0x07, 0x50, 0x00, 0x5D, 0x0B, 0x3F, 0x7F # TX 13dBm
]

paLevelList = [
            (0x17, 0x01), # -10dBm
            (0x1a, 0x01), # -09dBm
            (0x1d, 0x01), # -08dBm
            (0x21, 0x01), # -07dBm
            (0x25, 0x01), # -06dBm
            (0x29, 0x01), # -05dBm
            (0x2d, 0x01), # -04dBm
            (0x33, 0x01), # -03dBm
            (0x39, 0x02), # -02dBm
            (0x41, 0x02), # -01dBm
            (0x4b, 0x02), #  00dBm
            (0x56, 0x03), #  01dBm
            (0x63, 0x03), #  02dBm
            (0x71, 0x04), #  03dBm
            (0x80, 0x04), #  04dBm
            (0x22, 0x01), #  05dBm
            (0x27, 0x04), #  06dBm
            (0x2c, 0x05), #  07dBm
            (0x31, 0x06), #  08dBm
            (0x38, 0x06), #  09dBm
            (0x3f, 0x07), #  10dBm
            (0x48, 0x08), #  11dBm
            (0x52, 0x09), #  12dBm
            (0x5d, 0x0b), #  13dBm
            (0x6a, 0x0c), #  14dBm
            (0x79, 0x0d), #  15dBm
            (0x46, 0x10), #  16dBm
            (0x51, 0x10), #  17dBm
            (0x60, 0x12), #  18dBm
            (0x71, 0x14), #  19dBm
            (0x8c, 0x1c)  #  20dBm
]

mBaseFreqCfg = {
            RegionCfg.EUROPE : (0x42, 0x32, 0xCF, 0x82, 0x42, 0x27, 0x76, 0x12), # 860MHz
            RegionCfg.USA : (0x45, 0xA8, 0x31, 0x8A, 0x45, 0x9D, 0xD8, 0x19), # 905MHz (USA, Indonesia)
            RegionCfg.BRAZIL : (0x46, 0x6D, 0x80, 0x86, 0x46, 0x62, 0x27, 0x16),  # 915MHz (Brazil)
}

FREQ_STEP_KHZ  =     250   # channel step size in kHz

# detailed register infos from AN142_CMT2300AW_Quick_Start_Guide-Rev0.8.pdf
CMT2300A_MASK_CFG_RETAIN  =      0x10
CMT2300A_MASK_RSTN_IN_EN =       0x20
CMT2300A_MASK_LOCKING_EN  =      0x20
CMT2300A_MASK_CHIP_MODE_STA =    0x0F

CMT2300A_CUS_CMT10 =             0x09
CMT2300A_CUS_TX5   =             0x59
CMT2300A_CUS_TX8  =              0x5C
CMT2300A_CUS_TX9  =              0x5D
CMT2300A_CUS_TX10 =              0x5E

CMT2300A_CUS_MODE_CTL    =       0x60 

CMT2300A_CUS_MODE_STA     =      0x61 
CMT2300A_CUS_EN_CTL       =      0x62
CMT2300A_CUS_FREQ_CHNL    =      0x63

CMT2300A_CUS_IO_SEL    =         0x65

CMT2300A_CUS_INT1_CTL    =       0x66 

CMT2300A_CUS_INT2_CTL   =        0x67    # [4:0] INT2_SEL

CMT2300A_CUS_INT_EN     =        0x68  

CMT2300A_CUS_FIFO_CTL   =        0x69 

CMT2300A_CUS_INT_CLR1    =       0x6A # clear interrupts Bank1
CMT2300A_CUS_INT_CLR2    =       0x6B # clear interrupts Bank2
CMT2300A_CUS_FIFO_CLR    =       0x6C

CMT2300A_CUS_INT_FLAG   =        0x6D 

CMT2300A_CUS_RSSI_DBM   =        0x70

CMT2300A_GO_SWITCH      =        0x80
CMT2300A_GO_TX        =          0x40
CMT2300A_GO_TFS        =         0x20
CMT2300A_GO_SLEEP      =         0x10
CMT2300A_GO_RX        =          0x08
CMT2300A_GO_RFS       =          0x04
CMT2300A_GO_STBY      =          0x02
CMT2300A_GO_EEPROM   =           0x01

CMT2300A_STA_IDLE     =          0x00
CMT2300A_STA_SLEEP    =          0x01
CMT2300A_STA_STBY     =          0x02
CMT2300A_STA_RFS      =          0x03
CMT2300A_STA_TFS      =          0x04
CMT2300A_STA_RX       =          0x05
CMT2300A_STA_TX        =         0x06
CMT2300A_STA_EEPROM   =          0x07
CMT2300A_STA_ERROR    =          0x08
CMT2300A_STA_CAL      =          0x09

CMT2300A_INT_SEL_TX_DONE =       0x0A

CMT2300A_MASK_TX_DONE_FLG   =    0x08
CMT2300A_MASK_PKT_OK_FLG   =     0x01

class CMT2300A:
    def __init__(self, fifoCS: int, ctrlCS: int, freq: int):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.threewire = True
        self.spi.mode = 0
        self.spi.no_cs = True
        self.spi.max_speed_hz = freq
        self.fifoCS = fifoCS
        self.ctrlCS = ctrlCS
        self.mTxPending  = False
        self.mInRxMode   = False
        self.mCusIntFlag = 0x00
        self.mCnt        = 0
        self.mRqstCh     = 0xff
        self.mCurCh      = 0x20
        self.found       = False
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(fifoCS, GPIO.OUT)
        GPIO.setup(ctrlCS, GPIO.OUT)
        GPIO.output(fifoCS, 1)
        GPIO.output(ctrlCS, 1)

    def __del__(self):
        self.spi.close()

    def loop(self):
        if self.mTxPending:
            if CMT2300A_MASK_TX_DONE_FLG == self.__readReg(CMT2300A_CUS_INT_CLR1):
                if self.cmtSwitchStatus(CMT2300A_GO_STBY, CMT2300A_STA_STBY):
                    self.mTxPending = False
                    self.goRx()

    def goRx(self) -> CmtStatus:
        if self.mTxPending:
            return CmtStatus.ERR_TX_PENDING

        if self.mInRxMode:
            return CmtStatus.SUCCESS

        self.__writeReg(CMT2300A_CUS_INT1_CTL, CMT2300A_INT_SEL_TX_DONE)

        tmp = self.__readReg(CMT2300A_CUS_INT_CLR1)
        if 0x08 == tmp: # first time after TX a value of 0x08 is read
            self.__writeReg(CMT2300A_CUS_INT_CLR1, 0x04)
        else:
            self.__writeReg(CMT2300A_CUS_INT_CLR1, 0x00)

        if 0x10 == tmp:
            self.__writeReg(CMT2300A_CUS_INT_CLR2, 0x10)
        else:
            self.__writeReg(CMT2300A_CUS_INT_CLR2, 0x00)

        self.__writeReg(CMT2300A_CUS_FIFO_CTL, 0x02)
        self.__writeReg(CMT2300A_CUS_FIFO_CLR, 0x02)
        self.__writeReg(0x16, 0x0C) # [4:3]: RSSI_DET_SEL, [2:0]: RSSI_AVG_MODE

        if not self.cmtSwitchStatus(CMT2300A_GO_RX, CMT2300A_STA_RX):
            return CmtStatus.ERR_SWITCH_STATE

        self.mInRxMode = True
        return CmtStatus.SUCCESS

    
    def setPaLevel(self, level: int):
            if level < -10:
                level = -10
            if level > 20:
                level = 20

            level += 10 # unsigned value

            if level >= 15:
                self.__writeReg(CMT2300A_CUS_TX5, 0x07)
                self.__writeReg(CMT2300A_CUS_TX10, 0x3f)
            else:
                self.__writeReg(CMT2300A_CUS_TX5, 0x13)
                self.__writeReg(CMT2300A_CUS_TX10, 0x18)

            self.__writeReg(CMT2300A_CUS_TX8, paLevelList[level][0])
            self.__writeReg(CMT2300A_CUS_TX9, paLevelList[level][1])

    def getRx(self) -> tuple[CmtStatus, list]:
        if self.mTxPending:
            return CmtStatus.ERR_TX_PENDING, None
        
        if not self.mInRxMode:
            self.goRx()

        status = self.__readReg(CMT2300A_CUS_INT_FLAG)
        if 0x1b != (status & 0x1b):
            return CmtStatus.FIFO_EMPTY, None

        # receive ok (pream, sync, node, crc)
        if not self.cmtSwitchStatus(CMT2300A_GO_STBY, CMT2300A_STA_STBY):
            return CmtStatus.ERR_SWITCH_STATE, None
        
        self.found = True

        vals = self.__readFIFO()
        self.__readReg(CMT2300A_CUS_RSSI_DBM) - 128

        if not self.cmtSwitchStatus(CMT2300A_GO_SLEEP, CMT2300A_STA_SLEEP):
            return CmtStatus.ERR_SWITCH_STATE, None

        if not self.cmtSwitchStatus(CMT2300A_GO_STBY, CMT2300A_STA_STBY):
            return CmtStatus.ERR_SWITCH_STATE, None

        self.mInRxMode   = False
        self.mCusIntFlag = self.__readReg(CMT2300A_CUS_INT_FLAG)

        return CmtStatus.SUCCESS, vals

    def tx(self, buf) -> CmtStatus:
        if self.mTxPending:
            return CmtStatus.ERR_TX_PENDING

        if self.mInRxMode:
            self.mInRxMode = False
            if not self.cmtSwitchStatus(CMT2300A_GO_STBY, CMT2300A_STA_STBY):
                return CmtStatus.ERR_SWITCH_STATE

        self.__writeReg(CMT2300A_CUS_INT1_CTL, CMT2300A_INT_SEL_TX_DONE)

        # no data received
        self.__readReg(CMT2300A_CUS_INT_CLR1)
        self.__writeReg(CMT2300A_CUS_INT_CLR1, 0x00)
        self.__writeReg(CMT2300A_CUS_INT_CLR2, 0x00)

        self.__writeReg(CMT2300A_CUS_FIFO_CTL, 0x07)
        self.__writeReg(CMT2300A_CUS_FIFO_CLR, 0x01)

        self.__writeReg(0x45, 0x01)
        self.__writeReg(0x46, len(buf)) # payload length

        self.__writeFIFO(buf)

        if not self.found:
            self.mCurCh += 1
            if self.mCurCh > 40:
                self.mCurCh = 0
            
            self.__writeReg(CMT2300A_CUS_FREQ_CHNL, self.mCurCh)
        #if 0xff != self.mRqstCh:
        #    self.mCurCh = self.mRqstCh
        #    self.mRqstCh = 0xff
        #    self.__writeReg(CMT2300A_CUS_FREQ_CHNL, self.mCurCh)

        if not self.cmtSwitchStatus(CMT2300A_GO_TX, CMT2300A_STA_TX):
            return CmtStatus.ERR_SWITCH_STATE

        # wait for tx done
        self.mTxPending = True
        return CmtStatus.SUCCESS
    
    def cmtSwitchStatus(self, cmd, waitFor, cycles = 40) -> bool:
            self.__writeReg(CMT2300A_CUS_MODE_CTL, cmd)
            for i in range(0, cycles):
                time.sleep(0.0001)
                if waitFor == (self.getChipStatus() & waitFor):
                    return True
    
            # Serial.println("status wait for: " + String(waitFor, HEX) + " read: " + String(getChipStatus(), HEX));
            return False
    
    def reset(self, region) -> bool:
            self.mRegionCfg = region
            self.__writeReg(0x7f, 0xff) # soft reset
            time.sleep(0.03)

            if not self.cmtSwitchStatus(CMT2300A_GO_STBY, CMT2300A_STA_STBY):
                return False

            self.__writeReg(CMT2300A_CUS_MODE_STA, 0x52)
            self.__writeReg(0x62, 0x20)
            if self.__readReg(0x62) != 0x20:
                return False # not connected!

            for i in range(0, 0x18):
                self.__writeReg(i, cmtConfig[i])
    
            for i in range(0, 8):
                self.__writeReg(0x18 + i, mBaseFreqCfg[region][i])

            for i in range(0x20, 0x60):
                self.__writeReg(i, cmtConfig[i])

            if(RegionCfg.EUROPE != region):
                self.__writeReg(0x27, 0x0B)


            self.__writeReg(CMT2300A_CUS_IO_SEL, 0x20) # -> GPIO3_SEL[1:0] = 0x02

            # interrupt 1 control selection to TX DONE
            if CMT2300A_INT_SEL_TX_DONE != self.__readReg(CMT2300A_CUS_INT1_CTL):
                self.__writeReg(CMT2300A_CUS_INT1_CTL, CMT2300A_INT_SEL_TX_DONE)

            # select interrupt 2
            if 0x07 != self.__readReg(CMT2300A_CUS_INT2_CTL):
                self.__writeReg(CMT2300A_CUS_INT2_CTL, 0x07)

            # interrupt enable (TX_DONE, PREAM_OK, SYNC_OK, CRC_OK, PKT_DONE)
            self.__writeReg(CMT2300A_CUS_INT_EN, 0x3B)

            self.__writeReg(0x64, 0x64)

            self.switchFrequency(self.getBootFreqMhz() * 1000, self.getBootFreqMhz() * 1000)
            self.setPaLevel(5)

            if 0x00 == self.__readReg(CMT2300A_CUS_FIFO_CTL):
                self.__writeReg(CMT2300A_CUS_FIFO_CTL, 0x02) # FIFO_MERGE_EN

            if not self.cmtSwitchStatus(CMT2300A_GO_SLEEP, CMT2300A_STA_SLEEP):
                return False

            time.sleep(0.001)

            if not self.cmtSwitchStatus(CMT2300A_GO_STBY, CMT2300A_STA_STBY):
                return False

            if not self.cmtSwitchStatus(CMT2300A_GO_SLEEP, CMT2300A_STA_SLEEP):
                return False

            if not self.cmtSwitchStatus(CMT2300A_GO_STBY, CMT2300A_STA_STBY):
                return False

            # switchDtuFreq(WORK_FREQ_KHZ);

            return True

    def freq2Chan(self, freqKhz: int) -> int:
            if freqKhz % FREQ_STEP_KHZ != 0:
                return 0xff # error

            min, max = self.getFreqRangeMhz()
            if (freqKhz < min * 1000) or (freqKhz > max * 1000):
                return 0xff # error

            return (freqKhz - (self.getBaseFreqMhz() * 1000)) // FREQ_STEP_KHZ
    
    def switchFrequency(self, fromkHz: int, tokHz: int) -> bool:
            fromCh = self.freq2Chan(fromkHz)
            toCh = self.freq2Chan(tokHz)

            return self.switchFrequencyCh(fromCh, toCh)

    def switchChannel(self, ch: int):
            self.mRqstCh = ch
    
    def switchFrequencyCh(self, fromCh: int, toCh:int) -> bool:
            if (0xff == fromCh) or (0xff == toCh):
                return False

            self.switchChannel(fromCh)
            # sendSwitchChCmd(iv, toCh);
            self.switchChannel(toCh)
            return True

    def getBaseFreqMhz(self) -> int:
        baseFreq = {
            RegionCfg.EUROPE : 860,
            RegionCfg.USA : 905,
            RegionCfg.BRAZIL: 915,
        }
        return baseFreq[self.mRegionCfg]

    def getBootFreqMhz(self) -> int:
        bootFreq = {
            RegionCfg.EUROPE : 868,
            RegionCfg.USA : 915,
            RegionCfg.BRAZIL : 915
        }
        return bootFreq[self.mRegionCfg]

    def getFreqRangeMhz(self) -> tuple[int, int]:
        range = {
            RegionCfg.EUROPE : (860, 870),
            RegionCfg.USA : (905, 925),
            RegionCfg.BRAZIL : (915, 928)    
        }
        return range[self.mRegionCfg]

    def getChipStatus(self):
            return self.__readReg(CMT2300A_CUS_MODE_STA) & CMT2300A_MASK_CHIP_MODE_STA

    def __readReg(self, reg):
        GPIO.output(self.ctrlCS, 0)
        time.sleep(0.00001)
        ret = self.spi.xfer([reg | 0x80, None])
        time.sleep(0.00001)
        GPIO.output(self.ctrlCS, 1)
        return ret[1]
    
    def __writeReg(self, reg, value):
        GPIO.output(self.ctrlCS, 0)
        time.sleep(0.00001)
        self.spi.writebytes([reg & 0x7F, value])
        time.sleep(0.00001)
        GPIO.output(self.ctrlCS, 1)

    def __readFIFO(self):
        GPIO.output(self.fifoCS, 0)
        time.sleep(0.00001)
        len = self.spi.xfer([None])[0]
        time.sleep(0.00001)
        GPIO.output(self.fifoCS, 1)
        l = [None] * len
        for i in range(0, len):
            GPIO.output(self.fifoCS, 0)
            time.sleep(0.00001)
            l[i] = self.spi.xfer([None])[0]
            time.sleep(0.00001)
            GPIO.output(self.fifoCS, 1)
        return l

    def __writeFIFO(self, data):
        for i in data:
            GPIO.output(self.fifoCS, 0)
            time.sleep(0.00001)
            self.spi.writebytes([i])
            time.sleep(0.00001)
            GPIO.output(self.fifoCS, 1)
            time.sleep(0.001)

    