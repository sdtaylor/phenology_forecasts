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
bibliography: refs.bib
---

# Automated data-intensive forecasting of plant phenology throughout the United States

Shawn D. Taylor, Ethan P. White

Supplemental Information

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

## References
