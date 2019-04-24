---
csl: csl.csl
output:
  pdf_document:
    keep_tex: true
  html_document: false
geometry: left=3.5cm, right=3.5cm, top=2.25cm, bottom=2.25cm, headheight=12pt, letterpaper
header-includes:
- \usepackage{times}
- \usepackage{setspace}
- \usepackage{booktabs}
- \doublespacing
- \usepackage{lineno}
- \linenumbers
fontsize: 12pt
bibliography: refs.bak.bib
---

# Automated data-intensive forecasting of plant phenology throughout the United States

Shawn D. Taylor, Ethan P. White

**Supplemental Information**  
Phenology Model Descriptions  
Description of the phenology model weighting  
Description of the climate downscaling model   

**Supplemental Tables 1-2**

\newpage
### Phenology Model Descriptions

For all models, except the Linear and Naive models, the daily mean temperature $T_{i}$ is first transformed via the specified forcing equation. The cumulative sum of forcing is then calculated from a specific start date (either $DOY=1$ or using the fitted parameter $t_{1}$). The phenological event is estimated to be the $DOY$ where cumulative forcing is greater than or equal to the specified total required forcing (either $F^{*}$ or the specified equation). Parameters for each model are as follows: For the Linear model $\beta_{1}$ and $\beta_{2}$ are the intercept and slope, respectively and $T_{mean}$ is the average daily temperature between the spring start date and end using the parameters $Spring_{start}$ and $Spring_{start} + Spring_{length}$; in the Thermal Time model $F^{*}$ is the total accumulated forcing required, $t_{1}$ is the start date of forcing accumulation, and $T_{base}$ is the threshold daily mean temperature above which forcing accumulates; for the Alternating model $NCD$ is the number of chill days (daily mean temperature below 0$^{\circ}$C) from $DOY=1$ to the $DOY$ of the phenological event, $a$, $b$, and $c$ are the three fitted model coefficients; for the Uniforc model, is $F^{*}$ is the total accumulated forcing required, $t_{1}$ is the start date of forcing accumulation, and $b$ and $c$ are two additional fitted parameters which define the sigmoid function. For the Naive model $\beta_{1}$ and $\beta_{2}$ are the intercept and slope, respectively, for the average Julian day of a phenological event corrected for latitude. The Naive model is used as the long-term average for the annomally calculation.

\tiny

| Name         |                     DOY Estimator                    |                Forcing Equations                | Reference                                 |
|--------------|:----------------------------------------------------:|:-----------------------------------------------:|-------------------------------------------|
| Linear       |       $DOY = \beta_{1} + \beta_{2}T_{mean}$          |                        -                        | -                                         |
|||||
| Thermal Time |     $\sum_{t=t_{1}}^{DOY}R_{f}(T_{i})\geq F^{*}$     |   $R_{f}(T_{i}) = max(T_{i} - T_{base}, 0)$     | [@reaumur1735; @wang1960; @hunter1992]    |
|||||
| Alternating  | $\sum_{t=1}^{DOY}R_{f}(T_{i})\geq a + be^{cNCD(t)}$  |        $R_{f}(T_{i}) = max(T_{i}-5, 0)$         | [@cannell1983]                            |
|||||
| Uniforc      |    $\sum_{t=t_{1}}^{DOY}R_{f}(T_{i})\geq F^{*}$      | $R_{f}(T_{i}) = \frac{1}{1 + e^{b(T_{i}-c)}}$   | [@chuine2000]                             |
|||||
| Naive        |    $DOY = \beta_{1} + \beta_{2}Latitude$             |                                                 |                                           |

\normalsize

\newpage

### Description of the phenology model weighting

We used a weighted ensemble of the four models for each species and phenophase. The weights for each model within the ensemble were derived via stacking as described in -@dormann2018. The steps for calculating weights are as followed:

1. Subset the phenology data into random training/testing sets.
2. Fit each core model on the training set.
3. Make predictions on the testing set.
4. Find the weights which minimize RMSE of the testing set.
5. Repeat 1-4 for 100 iterations.
6. Take the average weight for each model from all iterations as the final weight used in the ensemble. These will sum to 1.
7. Fit the core models a final time on the full dataset. Parameters derived from this final iterations will be used to make predictions, which are then used in the final weighted average. 

The four phenology models are applied to each of the five climate ensemble, with a final predicted value derived as:

$$\frac{1}{5}\sum_{n=1}^{5}\sum_{i=1}^{4}w_{i}\widehat{DOY}_{n,i} $$

Where $n$ is the climate ensemble member, $i$ is the phenology model, $w$ is the phenology model weight, and $\widehat{DOY}$ the estimated Julian day. 

Uncertainty is the 95% confidience interval of the estimates from the five climate ensembles:

$$2 * \sqrt{var(\sum_{i=1}^{4}w_{i}\widehat{DOY}_{n,i})}$$

\newpage

### Description of the climate downscaling model

The Climate Forecast System Version 2 (CFSv2) is a coupled atmosphere-ocean-land global circulation model maintained by the National Oceanic and Atmospheric Administration (NOAA)[@saha2014]. The model tracks over 1000 global state variables of varying resolution and forecast length, such as ocean temperature and heights of pressure bands. Here we use the 2-meter temperature variable, which has a 6-hour timestep and a spatial resolution of 0.25 degrees latitude/longitude. The forecast is updated every 6 hours with the latest initial conditions and projected out 9 months. 

The CFSv2 also has a reanalysis available. A climate reanalysis is a run of the full model over a prior time period with constant assimilation of known conditions. In practice this allows for analysis of state variables which are not able to be measured (such as the 500mb height over the arctic in winter). Here it allows us to build a downscaling model using the CFSv2 model’s best estimate of past conditions of land surface temperature. These past conditions are regressed against finer grained “known” conditions from a different gridded dataset on a per pixel basis. We used the 2-m temperature output from the reanalysis from 1995-2015 as well as 4km daily mean temperature from the PRISM dataset [@prismdata] to build a downscaling model using asynchronous regression (Figure 1, E-G). The model and theory are described in -@stoner2013 and references therein. The CFSv2 data is first interpolated from the original 0.25 degree grid to a 4km grid using distance weighted sampling, then the following method is applied to each 4km pixel and calendar month.

Collect all daily mean temperature observations from 21 years of data from both the CFSv2 reanalysis and the PRISM dataset. This provides 588 - 641 points representing daily temperature for a single pixel and calendar month. 
In addition to the data from each calendar month, also include data for the 14 days prior and 14 days following the calendar month, adding an addition 588 data points (21*(14+14)). This helps account for future novel conditions.
Order each dataset by their rank, such that the lowest value from the PRISM dataset is matched to the lowest value from the CFSv2 reanalysis.
Fit a linear regression model.

The two parameters from the regression model are saved in a netCFD file which can later be referenced by location and calendar month (Figure 1, H). This downscaling model, at the scale of the continental U.S.A., is used to downscale the most recent CFSv2 forecasts to a 4km resolution during the automated steps. 

\newpage

### Table S1
Species and their associated phenophases used in the forecast system. Note not all species have forecasts for all phenophases due to data availabilty.
\tiny

|      |Species                   |Budburst     |Fall Colors  |Flowers      |Ripe Fruits  |
|-----:|:-------------------------|:------------|:------------|:------------|:------------|
|     1|Acacia greggii            |             |             |$\checkmark$ |             |
|     2|Acer circinatum           |$\checkmark$ |             |$\checkmark$ |             |
|     3|Acer macrophyllum         |$\checkmark$ |             |$\checkmark$ |             |
|     4|Acer negundo              |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|     5|Acer pensylvanicum        |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|     6|Acer rubrum               |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|     7|Acer saccharinum          |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|     8|Acer saccharum            |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|     9|Aesculus californica      |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    10|Alnus incana              |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    11|Alnus rubra               |$\checkmark$ |$\checkmark$ |             |             |
|    12|Amelanchier alnifolia     |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    13|Artemisia tridentata      |             |             |$\checkmark$ |             |
|    14|Berberis aquifolium       |             |             |$\checkmark$ |$\checkmark$ |
|    15|Betula alleghaniensis     |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    16|Betula lenta              |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    17|Betula nigra              |$\checkmark$ |             |$\checkmark$ |             |
|    18|Betula papyrifera         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    19|Carpinus caroliniana      |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    20|Carya glabra              |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    21|Celtis occidentalis       |$\checkmark$ |             |             |             |
|    22|Cephalanthus occidentalis |$\checkmark$ |             |$\checkmark$ |             |
|    23|Cercis canadensis         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    24|Chilopsis linearis        |             |             |$\checkmark$ |             |
|    25|Clintonia borealis        |             |             |$\checkmark$ |             |
|    26|Cornus florida            |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    27|Cornus racemosa           |$\checkmark$ |             |             |             |
|    28|Cornus sericea            |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    29|Corylus cornuta           |             |             |$\checkmark$ |$\checkmark$ |
|    30|Diospyros virginiana      |$\checkmark$ |             |             |             |
|    31|Fagus grandifolia         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    32|Fouquieria splendens      |             |             |$\checkmark$ |             |
|    33|Fraxinus americana        |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    34|Fraxinus pennsylvanica    |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    35|Gaultheria shallon        |             |             |$\checkmark$ |$\checkmark$ |
|    36|Ginkgo biloba             |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    37|Gleditsia triacanthos     |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    38|Hamamelis virginiana      |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    39|Ilex verticillata         |$\checkmark$ |             |$\checkmark$ |             |
|    40|Juglans nigra             |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    41|Liquidambar styraciflua   |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    42|Liriodendron tulipifera   |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    43|Magnolia grandiflora      |$\checkmark$ |             |$\checkmark$ |             |
|    44|Maianthemum canadense     |             |             |$\checkmark$ |             |
|    45|Nyssa sylvatica           |$\checkmark$ |             |$\checkmark$ |             |
|    46|Ostrya virginiana         |$\checkmark$ |             |$\checkmark$ |             |
|    47|Oxydendrum arboreum       |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    48|Platanthera praeclara     |$\checkmark$ |             |$\checkmark$ |             |
|    49|Platanus racemosa         |$\checkmark$ |             |$\checkmark$ |             |
|    50|Populus deltoides         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    51|Populus fremontii         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    52|Populus tremuloides       |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    53|Prunus americana          |$\checkmark$ |             |$\checkmark$ |             |
|    54|Prunus serotina           |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    55|Prunus virginiana         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    56|Quercus agrifolia         |$\checkmark$ |             |$\checkmark$ |             |
|    57|Quercus alba              |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    58|Quercus douglasii         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    59|Quercus gambelii          |$\checkmark$ |$\checkmark$ |             |             |
|    60|Quercus laurifolia        |$\checkmark$ |             |             |             |
|    61|Quercus lobata            |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    62|Quercus macrocarpa        |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    63|Quercus palustris         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    64|Quercus rubra             |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    65|Quercus velutina          |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    66|Quercus virginiana        |$\checkmark$ |             |$\checkmark$ |             |
|    67|Rhododendron macrophyllum |$\checkmark$ |             |$\checkmark$ |             |
|    68|Robinia pseudoacacia      |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    69|Salix hookeriana          |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    70|Salix lasiolepis          |$\checkmark$ |             |$\checkmark$ |             |
|    71|Sassafras albidum         |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    72|Sorbus americana          |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    73|Tilia americana           |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    74|Ulmus americana           |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    75|Umbellularia californica  |$\checkmark$ |             |$\checkmark$ |             |
|    76|Vaccinium corymbosum      |$\checkmark$ |$\checkmark$ |$\checkmark$ |             |
|    77|Vaccinium membranaceum    |             |             |$\checkmark$ |$\checkmark$ |
|    78|Yucca brevifolia          |             |             |$\checkmark$ |             |
|      |**Total**                 |**67**       |**47**       |**72**       |**4**        |

\normalsize
\newpage

### Table S2
Species and their associated phenophases evaluated from the 2019 season. Data are from the USA National Phenology Network from Jan. 1, 2019 - May 5, 2019.

\tiny  

|      |Species                 |Phenophase | Total Observations| Mean Julian Day|
|-----:|:-----------------------|:---------------|---------:|--------:|
|     1|Acer circinatum         |Budburst        |       682|     87.0|
|     2|Acer circinatum         |Flowers         |        62|     96.0|
|     3|Acer macrophyllum       |Budburst        |       186|     84.0|
|     4|Acer macrophyllum       |Flowers         |        62|     90.0|
|     5|Acer negundo            |Budburst        |        93|     94.0|
|     6|Acer negundo            |Flowers         |        62|     52.0|
|     7|Acer rubrum             |Budburst        |       651|     80.0|
|     8|Acer rubrum             |Flowers         |       589|     68.0|
|     9|Acer saccharinum        |Budburst        |        31|     86.0|
|    10|Acer saccharinum        |Flowers         |        62|     88.0|
|    11|Aesculus californica    |Budburst        |        31|     59.0|
|    12|Alnus rubra             |Budburst        |        62|     72.0|
|    13|Amelanchier alnifolia   |Budburst        |        31|     83.0|
|    14|Betula nigra            |Flowers         |        31|     87.0|
|    15|Carpinus caroliniana    |Budburst        |        31|     40.0|
|    16|Carpinus caroliniana    |Flowers         |        31|     40.0|
|    17|Carya glabra            |Budburst        |        62|     46.0|
|    18|Carya glabra            |Flowers         |        31|     85.0|
|    19|Cercis canadensis       |Budburst        |       155|     72.0|
|    20|Cercis canadensis       |Flowers         |       124|     53.0|
|    21|Cornus florida          |Budburst        |       620|     83.0|
|    22|Cornus florida          |Flowers         |       186|     74.0|
|    23|Cornus sericea          |Budburst        |        62|     84.0|
|    24|Corylus cornuta         |Flowers         |        30|     76.0|
|    25|Fagus grandifolia       |Budburst        |        31|     43.0|
|    26|Hamamelis virginiana    |Budburst        |        31|     89.0|
|    27|Liquidambar styraciflua |Budburst        |       310|     68.0|
|    28|Liquidambar styraciflua |Flowers         |        31|     47.0|
|    29|Liriodendron tulipifera |Budburst        |       279|     83.0|
|    30|Liriodendron tulipifera |Flowers         |        62|     84.0|
|    31|Magnolia grandiflora    |Budburst        |        93|     74.0|
|    32|Nyssa sylvatica         |Budburst        |        31|     68.0|
|    33|Populus tremuloides     |Flowers         |        62|     86.0|
|    34|Prunus serotina         |Budburst        |       403|     75.0|
|    35|Prunus serotina         |Flowers         |       217|     49.0|
|    36|Prunus virginiana       |Budburst        |        93|     84.0|
|    37|Quercus agrifolia       |Budburst        |       124|     72.0|
|    38|Quercus alba            |Budburst        |        93|     62.0|
|    39|Quercus alba            |Flowers         |        31|     81.0|
|    40|Quercus laurifolia      |Budburst        |       279|     50.0|
|    41|Quercus rubra           |Budburst        |        62|     59.0|
|    42|Quercus virginiana      |Budburst        |       217|     52.0|
|    43|Quercus virginiana      |Flowers         |       155|     59.0|
|    44|Sassafras albidum       |Flowers         |        31|     61.0|
|    45|Ulmus americana         |Budburst        |       124|     77.0|
|    46|Vaccinium corymbosum    |Budburst        |       155|     66.0|
|    47|Vaccinium corymbosum    |Flowers         |       186|     58.0|
|      |Total                   |                |      7067|     72.8|

\normalsize
\newpage

##References
