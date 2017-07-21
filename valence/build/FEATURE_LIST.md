# Agilent GCMS Data Checklist
### What devices are we targeting ###
For the current AgilentGcms class we are targeting all of Agilents GCMS devices. More specifically, any Agient GCMS which produces a .MS file (which I assume is GCMSs of them). 

Additionally, I belive their LC-MS (liquid chromotography-mass spectrometry) and their ICP-MS (insane clown posse-mass spectrometry) all will use .MS formats as they use the same aquitiion, Mass Hunter, and analysis, ChemStation, software for all three GCMS, LCMS and ICPMS techniques.

[mass hunter/chemstation video](http://www.agilent.com/en/products/software-informatics/masshunter-suite/masshunter-overview)
[mass hunter/chemstation info](http://www.agilent.com/en/products/software-informatics/masshunter-suite/masshunter/masshunter-software-with-msd-chemstation-da)

### Files and file types in the .D folder ###
 - **.txt**: these will be user reports, or files which contain system configurations and run settings, generally we wont worry about them. I am unsure what .txt files are default generated, pretty sure there will always be a `acqmeth.txt`
 - **.ms**: this is the main data file, its is the one we will be primarily concerned with
 - **.csv**: the csv will contain the library report data and the integration data as long as the user presses the two buttons necssary to calculate these values 
 - **.ch**: this one im not sure. it may contain the FID chromatogram. It could have the same encoding as the .MS but we will need to look at it.
 - **.ini**: these are *configuration settings*, for the instrument, we arent concerned with them.
 - **.M**: this folder looks like an exact copy of the method for the data aquistion, basically  nothing useful unless you have and Agilent GCMS
