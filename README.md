# C3G_Search_Project
Compares user input to online EBI database and returns the location of the queried files. 

## Valid Search Parameters
Search parameters must be in the first line of the query file. Searches must include at least one of these parameters, copied exactly. 

### Regular search Parameters
Regular searches match the string in the query file to the metadata associated with each IHEC ID. All associated instances will be flagged as matches. 

- ihec_id (Note: a different version will not be considered a match)
- project
- age_min
- age_max
- age_exact
- gender
- species
- markers
- biomaterial_provider
- primary_id
- secondary_id
- assay_type
- experiment_type
- archive

### Keyword Search parameters:
All items in input must be satisfied, but there may be extra keywords in the search element. For instance, a dataset may have "cord blood" listed as its tissue type. A keyword search using either "cord", "blood", or both will yield a match. However, if the dataset only has "blood" as its tissue type, a search for "cord blood" will not result in a match. 

- donor_id (stored as donor id, donor_id, or sample_id on the EBI Database)
- tissue_keywords
- donor_ethnicity_keywords
- disease_keywords

### Accepted keywords:
| abdominal | absorptive | activated | adenoma | adipocyte | adipose | adrenal | alpha |
| amnion | amygdala | angular | anterior | aorta | aortic | area | artery |
| ascending | astrocyte | atrium | auricular | band | basal | basophilic | beta |
| blast | blastocyst | blood | body | bone | brachiocephalic | brain | breast |
| brodmann | bronchial | brown | bulb | bvsc | capillary | cardiac | carotid |
| caudate | cava | cd14 | cd16 | cd19+ | cd25 | cd3 | cd34 | 
| cd34+ | cd38 | cd4 | cd4+ | cd41 | cd42 | cd49f | cd56 | 
| cd8 | cd8+ | cell | center | central | cerebellum | chromosome | cingulate |
| class | classical | clone | colon | colonic | colony | common | continued |
| conventional| cord | coronary | cortex | cortical | culture | cytotoxic | cytotrophoblast |
| d2 | d4 | d6 | dendritic | derived | dermis | differentiated | dim |
| double | duodenal | duodenum | early | ectoderm | effector | 
embryo
embryonic
eminence
endocardial
endocrine
endoderm
endometrial
endometrium
endothelial
endothelium
eosinophil
epiblast
epidermal
epithelia
epithelial
epithelium
erythroblast
erythrocyte
erythroid
esophagus
examined
extravillous
facial
fat
fetal
fibroblast
fluid
follicular
forebrain
foreskin
form
forming
foveolar
from
frontal
gain
gains
ganglionic
gastrocnemius
gastroesophageal
germ
germinal
gland
granulocyte
great
gyrus
h18
have
heart
helper
hematopoietic
hepatocyte
hepatocytes
hindbrain
hippocampus
hla
htert
hterts
human
immature
induced
inflammatory
intestine
ipsc
islet
isolated
keratinocyte
kidney
killer
lamina
large
late
layer
leg
limb
lineage
liver
lobe
luminal
lung
lymph
lymphocyte
lymphocytes
lymphoid
macrophage
mammary
marrow
marroy
matrix
mature
medialis
megakaryocyte
melanocyte
melanocytes
memory
mesangial
mesenchymal
mesenchyme
mesoderm
mesodermal
metamyelocyte
microvascular
midbrain
middle
mixed
monocyte
mononuclear
mucosa
mucous
multipotent
muscle
muscularis
myelocyte
myeloid
myoblast
myoepithelial
naive
natural
negative
neoplastic
nerve
neural
neuron
neurosphere
neutrophil
neutrophilic
nigra
node
normal
nucleus
occipetal
olfactory
oocyte
original
osteoblast
osteoclast
other
ovary
pad
pancreas
parathyroid
parenchymal
passage
patch
peripheral
peyer
phase
placenta
plasma
plate
pluripotent
podocyte
polychromatophilic
population
positive
prdm14
preadipocyte
precursor
predisposed
prefrontal
primary
primordial
progenitor
progenitors
proliferating
prominence
propria
prostate
psoas
pulmonary
rapidly
rectal
rectosigmoid
rectum
region
regulatory
resting
right
saphenous
satellite
segmented
selected
sigmoid
skeletal
skin
small
smooth
sperm
sphincter
spleen
squamous
stem
stomach
stroaml
stroma
stromal
subclavian
subcutaneous
substantia
superior
suprapubic
surface
switched
synovial
temporal
temra
terminally
testes
testis
thoracic
thymocyte
thymus
thyroid
tibial
tissue
tobeupdated
tonsil
transverse
trophoblast
trunk
tube
umbilical
unknown
unswitched
upon
upper
uterus
vagina
vein
vena
venous
ventricle
vessels
was
which
white
wt



abuse
activated
acute
adenocarcinoma
adenoma
adenosquamous
adipositas
alport
ampulla
anaplastic
anoxia
apparently
arising
arthritis
asthma
ataxia
atcc
autism
bardet
bft
biedl
bipolar
bleeding
blood
blunt
bone
brain
Breast
cancer
carcinoma
carcinomanephropathy
carcinome
cardiomyopathy
carotid
cavernous
cell
center
centroblastic
centrocytic
cervical
chromosome
chronic
classical
colitis
colloid
colon
colorectal
component
congenital
cortical
cortison
crl
cystic
defects
deficiency
diabetes
diffuse
disease
diseased
diverticular
diverticulitis
duplication
dystrophy
embryonal
erythematosus
etv6
ewing
eye
fatty
fibrocystic
follicular
force
free
frontal
gastric
genetic
germinal
gland
glioblastoma
goiter
grade
head
health
healthy
hemangioma
hepatocellular
hereditary
histiocytic
hodgkin
human
hydatidiform
hyperinsulinia
hypertrophic
hypothyroidism
igak
immune
immunoblastic
immunoglobulin
intestine
intraductal
intrahepatic
iron
kabuki
kidney
klatskin
known
lambda
large
left
leigh
leukemia
line
liver
lobe
localized
lupus
lymphoblastic
lymphocytic
lymphoma
macular
malignant
mammary
mantle
marrow
medication
mellitus
mesazilin
metastasis
metastatic
mole
monogenic
mucinous
multiforme
multiple
muscosa
myelogenous
myeloid
myeloma
myoma
myositis
neoplasm
neoplasmnormal
nephropathy
neuroblastoma
neuroendocrine
oligodendroglial
oligodendroglioma
oncocytoma
osteomylitis
p13q22
pancreatic
papillary
paraplegia
peripheral
pigmentosa
platelet
pluripotent
pneumonia
polysubstance
primary
progressed
prolymphocytic
promyelocytic
pseudopapillary
rare
refractory
renal
retinitis
rheumatic
rheumatoid
salofalk
sarcoma
scleroderma
sigma
solid
spastic
spectrum
sporadic
steatosis
stenosis
submaxillar
symptomatic
syndrome
systemic
temporal
thyroid
trauma
trisomy
tumor
type
ulcerative
unknown
usher
vater
xald



## Creating A Query File
A query file is one of two parameters passed into the search function. It is a tab-delimited file containing all information you are searching for. The first line of the file contains all seach parameters, and subsequent lines contain values to be matched. All values on one line must be satisfied in order to be considered a match (i.e. "and" function). 

### Sample Input

project gender  assay_type  tissue_keywords
blueprint   chip-seq  cancer
  male  rna-seq 

The first search returns all files from 



# Updating Local Copy of EBI Database
