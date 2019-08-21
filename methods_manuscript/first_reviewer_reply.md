---
output:
  pdf_document: default
  html_document: default
---
Dear Dr. Ward,  
We would like to thank the two reviewers for all their constructive and positive feedback. We have addressed their comments in regards to clarifying various methods and pipeline descriptions throughout the manuscript. More detailed responses are below, with our comments in bold, or enclosed in ** if reading the plain text version.   

Regards,  
Shawn Taylor & Ethan White


# Reviewer: 1
Comments to the Author

This manuscript describes the operationalization of an automative plant phenology forecasting system for 78 species across the continental U.S. The authors clearly document a reproducible pipeline for implementing their forecasts, allowing other developers to leverage off their work. This work is timely given the scientific community’s increased interest in ecological forecasting, and it will make a valuable contribution to the literature. 

Major concerns.
-My only major critique is that as a reader who isn’t an expert in phenology forecasting, I was left unsure of the major improvements this system has over other existing systems. In the introduction the authors mention that most phenology forecasts focus on spring indices as opposed to phenophase level forecasts. Does this system also have the finest spatial scale? The most number of species? The large spatial coverage? Would be good to point to the outputs of other phenology forecasts and clearly describe the improvements made in the present study. 

**There is only one other phenology forecast that we are aware of (described in Carrillo et al. 2018). In the 3rd introduction paragraph we have emphasized this and the other systems limitations (1° resolution, not for specific species) to give readers a baseline to compare to.**

### Abstract.

Line 11. Would it be possible to include a more specific definition of phenology for readers that are unfamiliar with the term? Something like: “Phenology – the timing of cyclical and seasonal natural phenomena such as flowering and leaf out - …”

**We have added this, thank you for the suggestion**

Line 12-13. Suggest: “…with impacts on human activities like environmental management, tourism, and agriculture.”

**We have added this, thank you for the suggestion**

Line 15. What is mean by broad scale? A large volume of data? Broad spatial coverage? Broad temporal coverage?

**Data, specifically those from citizen science efforts, has amassed at large spatial scales (throughout the entire USA for our study), temporal scales (> 10 years), and taxonomic scales (> 1000 species monitored). We have clarified this statement in the abstract.**

Line 17. Volume should be plural.

**Fixed.**

### Introduction.

Line 28. Again, here would be good to provide a more in-depth description of phenology.

**We have repeated the description suggested for the abstract here.**

Line 37. Would be good to conclude this paragraph with a problem statement similar to the one in the abstract. Something along the lines of: “However, due to the challenges of automatically integrating, predicting, and disseminating large volumes of data, there are limited examples of applied phenology forecast systems.”

**Thank you for the excellent suggestion, we have added this sentence to the first introduction paragraph.**

Line 42. Perhaps this is discussed elsewhere in the manuscript, but would be interesting to include a discussion of the timing of plant response to changes in the weather. For example, how long does a temperature spike need to persist to initiate a leaf-out event? If we have one warm day, is that long enough to trigger a change in phenology, or do warmer temperatures need to persist for days or weeks? Is the plant response immediate, or is there a time lag? And how does this interplay with climatological triggers? Presumable plants are also responding to non-weather drivers, such as changing light availability. 

**We agree a discussion of phenological drivers would be of interest to some researchers, as this is the basis of the majority of phenological research (see Chuine and Régnière 2017 for a thorough review). Our study describes the implementation of a forecast system, itself meant primarily to inform end-users as opposed to studying phenological drivers, and as such we feel a discussion like this is out of scope.**

Line 49. Near-term or near term. Select one for consistency throughout (abstract uses near-term).

**We have corrected this to near-term throughout the manuscript.**

Line 51. Please include an example of an integrate spring index. I’m assuming it’s aggregated across multiple species and multiple phenophases?

**We've included a brief description of the spring index model here. It's described fully in Schwartz et al. 2013 (newly cited)**

Line 57-60. Would be good to be more explicit about the types of scales being discussed. Line 59 makes it sound like this is a discussion of spatial scale. But I assume this present analysis is also more challenging given that it includes a large number of species and multiple types of phenologic events, and as is stated in the following sentences, the high spatial resolution.

**We have clarified the important scales here as either spatial (ie. single site or continental) or taxonomic (just a few to numerous species)**

Lines 50-69. Suggest restructuring this paragraph to make it easier to grasp its purpose, which I believe is to demonstrate the limits of current phenology forecasts, and why to date we haven’t seen a phenology forecast at the scale of the one in the manuscript. Perhaps something like: “For applied use in planning exercises, plant phenology forecasts are most informative when produced at species- and phenophase-levels, over large spatial scales, and at high spatial resolutions. However forecasting at this level of detail is challenging due to the need for advanced computation tools to build and maintain automative forecasting systems.” And then go on to explain your points on integrated spring indices, regional forecasts, downscaled seasonal climate forecasts. 

**We have incorporated this suggestion into the paragraph along with the prior two comments.**

Line 77. Would it be accurate to say “automating the pipeline to update forecasts with a sub-weekly frequency”? In my work this step would be producing a new forecast for days further in the future, e.g. 6 months + 1 day, 6 months + 2 days, etc. But I believe your system is updating/improving the same forecast for a specific phenophase event as more data comes in. This is a subtle distinction, but I think helpful for readers to grasp the structure of your system.

**Sub-weekly frequency is a clearer description and we have incorporated it. We also clarified that these 5 steps are part of the system construction, as opposed to the 3 steps which make up the automated pipeline**

### Methods

Line 92. Suggest being specific in the usage of scale. Here it refers to spatial scale.

**We have clarified this as spatial scale.**

Line 93. What range? The prediction range (the continental US) or the species specific range?

**We clarified that this is the species specific range.**

Lines 94-96. Over what time range?

**The time range of the training data is 2009-2017 and is specified later in this paragraph.**

Line 99. What phenophases did you select for modeling?

**We have clarified that we selected budburst, flowering, and fall colors for modelling. There are also several fruit forecasts used, which are contributed models and were not built using USA-NPN data, and this has been clarified as well.**

Line 106. What does daily mean temperature refer to? The mean temperature in a 24 hour period? A climatological daily mean?

**It refers to the mean temperature in a 24 hour period. We've clarified this in the text.**

Line 107. What is the PRISM dataset? Is it modeled? Remote sensing data? Some integrated product?

**PRISM is a gridded dataset which interpolates on the ground measurements. We have added this description to the text.**

Line 108-109. Is temperature time-matched to the observations? E.g. for a given record, was the temperature at the time and place of the record used a predictor?

**Yes, phenology models use all daily temperature records leading up to the day of budburst (or other phenophase). We have expanded the description of phenology modeling to help clarify this for readers.**

Line 110. Ensembles also help remove model-specific biases.

**Thank you, we have added this point.**

Line 120-121. Remind the reader how much of each you are working with, e.g. 78 species, four models, xx# phenophases.

**We clarified here that there are 190 unique phenological model ensembles. This is less than the species x phenophase count as not every species/phenophase combination had enough data available. Table S1 outlines the specifics and 190 is the sum of the final row.**

Line 131. What are accumulated growing degree days? Perhaps specify in the phenology modeling section.

**We have expanded the description of phenology models and growing degree days to help clarify this for readers (2nd Phenology Modelling paragraph).**

Line 172. Unsure what a five member ensemble is.

**We have clarified that this is an ensemble prediction combining five different forecasts of daily mean temperature.**

Line 175. What is the range of the time dimension? Now to now + 9 months (the projected period of the CFSv2 forecasts?)

**Now + 9 months is correct and we have clarified this in the text.** 

Line 180. Where does information on range come from? Published literature? The extent of the species specific observations?

**This comes from a commonly used dataset of North American tree ranges and it as been cited here.**

Line 187-189. Suggest editing: “The members of the climate ensemble each produce a different temperature forecast due to differences in initial conditions.”

**We have added this suggestion.**

Line 190. Five

**Fixed.**

Line 193. This is really cool. And a really valuable component of the system.

**Thank you.**

Line 196. Here or elsewhere in the paragraph remind readers of the website URL.

**We have added a URL here.**

Line 196-197. Here and elsewhere in the methods select one type of voice. “We built a website” vs “a website was built”. 

**We changed to active voice here, and elsewhere throughout the manuscript where appropriate.**

Line 210. And the building of the downscaling model. Good to specific that you are referencing both the species/phenotype specific models and the downscaling model.

**We have clarified the model fitting includes both phenology and downscale models.**

Line 211. Con job. No apostrophe. 

**Fixed.**

Line 212. “The cron job first runs a script that acquires the newest climate observations...” If someone is reading this paper to learn how to build their own forecasting system, it will help them to have an understanding of how your code block is organized by scripts. Or is everything in one master script? Also what’s the timing of the cron job – first thing in the morning? 

**We clarified the exact process here as the cron job initiates a master script which subsequently runs other scripts. The details beyond that can be seen by interested persons by looking at the scripts in the code repository.**

Line 229. Specify that these are R packages.

**Fixed.**

### Discussion

Line 280. “…entry barrier of operationalizing ecological models for decision making…”

**Fixed.**

Lines 272-285. Hard to understand the main message of this paragraph.  Suggest maintaining first sentence, and then as a second sentence something like: “To facilitate the development of ecological forecasts, we need xxxxxx (applied examples, discussion of the development methodologies, standardized models, software packages, etc).” And then use the remainder of the paragraph to expand on each of the components.

**We intended this paragraph to emphasize the need for studies describing forecast implementation. We have incorporated this suggestion and re-written this paragraph to be more clear about this.**

Lines 291-292. How generalizable is your code? Give the reader an indication of how broadly it could be used. Other taxa? Other climate models? Marine forecasts?

**The portability of code here refers specifically to the pyPhenology package, which is broadly usable in other phenology studies and we have clarified this.**

Line 292. Automatically

**Fixed.**

Line 300. Where does 190 come from? 78 species x 4 phenologies = 312.

**Not all phenophases are implemented for each species due to data limitations. 190 is the total number of combinations of species and phenophases used and is the sum of the final row of Table S1. This is now better explained in updated Phenology Modeling section.**

Line 301. Four different phenology models -> are these the four models in the ensemble?

**Correct. We have changed this to "sub-models" to better reflect that.**

Line 317. R shiny applications are one avenue for developing interactive maps. Here is a particularly impressive one: https://ctmm.shinyapps.io/ctmmweb/ . 

**We agree Shiny is an important tool that deserves more attention. While we didn't use it in our system, it was utilized in the system by Welch et al. 2019 and we have highlighted that.**

Line 356-358. This is an important point that I think could be stated a little more directly. While there are many published examples of species distribution models, it’s much harder to find published examples of system operationalization, making it challenging to find templates to follow. Operationalization/implementation is a key component of producing applied tools, and it’s important that pipelines are documented in the literature. Also could stress here that it’s important to make code blocks public so that other developers can leverage them.

**Thanks for the suggestion. We have emphasized here the lack of similar studies, and how making our code available is also an important aspect.**

Lines 364-366. You’ve already thoroughly explored areas of improvement, and I think it sells your system short to repeat here. Suggest instead focusing on what makes this system novel, e.g. multi-species, unaggregated phenotypes, large spatial coverage, fine spatial resolution, etc. Conclude with what you’ve done well, not what you could have done better. 

**Thank you. We have removed the wording here which references areas for improvement.**
____________________________________


# Reviewer: 2
Comments to the Author

Taylor and White present a novel predictive model for flowering time in the USA.  In this paper, they successfully integrate phenological data collected by in-situ observers in the National Phenology Network and climate data to make predictions about multiple phenophases for 78 species six months in advance.  The authors have not only created novel and useful methods that apply to a wide range of ecological applications, but they have made a novel contribution to our understanding of phenological changes. I am optimistic that further development of these methods will enable excellent research across many realms of ecology. 

I  am recommending that the manuscript “Automated data-intensive forecasting of plant phenology throughout the United States” by Taylor and White to be accepted with minor revisions.

The authors have used free and open source tools to build a automated system to forecast phenology at continental scales and provide the data outputs to the public. The authors present a detailed report of their forecasting pipeline, which other users will find informative. They report how to fit the phenological models, acquire and appropriately sample the climate data, make predictions, and serve those predictions to public and well as serving the model code via github. 

The dataset and tools they have created are capable of answering many more interesting questions in ecology.  For example, do most species respond to temperature in the same direction and magnitude?  How variable are species responses?  Are certain phenophases more sensitive to temperature shifts? Does this vary by species?

This paper is well written and the language is astonishingly clear for a paper that focuses on ecological modeling.  Well done. I have a few minor suggestions that will clarify certain parts of the manuscript.

**Thank you!**

Line 44: For someone unfamiliar with modeling lingo, “operationalization” isn’t clear.

**We have changed this instance of “operationalization” to "deployment" for better flow, but have described “operationalization” in the last introduction paragraph.**

Line 46: Be explicit that the outer predictive range of this paper is 6 months. Here the authors say “this time horizon” and elsewhere “near-term,” without really clarifying what the time horizon is. 

**See the note below about the time frames and the 6 month limit. This has been clarified in the final Introduction paragraph.**

Line 51: “integrated spring indices” is unclear and would be better if explained a bit more in the text. 

**This term has been clarified.**

Line 70: drop the words “near term” Unnecessary jargon.

**Near-term is an important distinction to make here and we have kept it in place. Ecological forecasts which make predictions for 10+ years into the future are extremely common, yet have several downsides (such as lack of evaluation potential). Near-term forecasts (for events happening less than 1 year into the future) overcome many of these issues yet are still relatively rare (see Dietze et al. 2018 for a thorough review).**

### Phenological Modeling
Line 100: explain what “Individual Phenometrics” are.

**We have described that this is a data product title from USA-NPN and what it provides.**

Lines 100-107: This section contributes to a little bit of confusion regarding dataset time frames.  Here the authors say that they extracted NPN data from 2009-2017. But then the authors state that only records with at least 30 observations were included.  Since some species have a large range, and the time scale spans 8 years, are these 30 observations spanning both time and space.  That seems sparse. If that is not the meaning of lines 105-106 please clarify. 
Is the PRISM data spanning the same time period? 

**This is correct, the USA-NPN data spans 8 years and includes the continental USA. We have clarified that the PRISM data corresponds to the same 2009-2017 timeframe. We have previously evaluated the use of a 30 observation threshold in this dataset for fitting phenology models (Taylor et al. 2019 [https://doi.org/10.1002/ecy.2568](https://doi.org/10.1002/ecy.2568)) and found this to be a reasonable number of data points for achieving an accurate model fit. Specifically, see figure S5 and table S1 in Taylor et al. 2019. For example with the species Acer circinatum, models for budburst built using USA-NPN data (n=39) had very similar cross-validation errors to models built using phenology data from H.J. Andrews LTER (n=266). The USA-NPN data likely provides a large amount of predictive power from observations being spatially dispersed.**

Line 121: How many phenophases?  This is reported in the tables, but it should be added in the text. 

**We added which specific phenophases we used in the Phenology Modelling section.**

Line 125: Should json be JSON?

**Correct, we changed it to JSON.**

Line 131: Define accumulated growing degree days.

**We added a clearer explanation of how growing degree days are calculated in the Phenology Modelling section (2nd paragraph).**

Lines 163-166: “perform operations” and “this type of operation” are largely unexplained in this section.  It’s not abundantly clear what is happening here. 

**We've clarified these statements so that they refer specifically to big-data operations involving the CFSv2 climate dataset.**

Line 200: The maps show the predicted event for what time in the future?  Is it always 6 months out or can you specify the forecast?  Specify the “when” here.

**The "time-frame" of a phenology forecast can be confusing as the response variable itself is date. For example if a forecast made on Jan. 1 predicts Species A to flower on March 1, and Species B to flower on May 1, these correspond to 60 and 90 day lead times, respectively. The 6-month limit we use in the manuscript is essentially an upper limit on this lead time, as the majority of budburst and flowering in the US is over by the summer solstice in June, and we begin making forecasts December 1. This has been clarified in the final Introduction paragraph.**

Line 203: I think a word is missing making this sentence read poorly.

**This sentence has been reworded.**

Lines 196 - 208: I think this dissemination section could be strengthened if you turned figure 2 into three discrete panels; A, B, and C.  Then you could reference each map in figure 2 separately when discussing them in this section.  I thought the caption on Fig. 2 was weak and making this change will also correct that. It was not very clear what the different maps were showing from reading only the figure caption. 

**We cannot split this figure into subpanels since it's a direct screenshot of the website. Instead we've added A-D labels to highlight the different aspects of it, which are then referenced in the text and caption.**

Lines 208: Please clarify where the “long term, spatially corrected average date of he phenological events” is coming from.  It is not clear if this is the phenological model made from the NPN data from 2009-2017.  

**This represents the output of a linear model where DOY ~ Latitude, which amounts to the long term average (from the NPN data) with a correction for latitude. We've clarified this in the phenology modelling section and phenology model supplement. As noted, this is only used in generating the anomaly maps and not anywhere else in the pipeline.**

Evaluation section lines 239-249: I think the first paragraph here needs more clarity.   The authors need to clearly state “We used 2019 data to check the accuracy of our predictions.” This is the point of this section but it’s only alluded to in fancy sentences that obscure the point. 
Was all data from NPN in the time range downloaded of only those pertaining to the taxa in your predictive model? If they are different, is that justified and meaningful?

**We've clarified that we used 2019 observations for the evaluation, and that these were constrained to only instances that forecasts were performed for. If a species/phenophase combination was in the downloaded dataset but not in our forecast system it was not among the final 1581 observations used in the evaluation.**

Line 328: “it’s” should be “its”

**Fixed.**

Line 361: It might be useful to say if the user can access the metadata behind each forecast.

**All original netCDF files generated by the forecast system, and 2019 evaluation data, are available in the Zenodo repository, and this has been noted in the Automation section.**

At some point in the discussion the authors should address if future models will incorporate more than temperature. 

**We've added text in the 2nd to last discussion paragraph about the potential to integrate daylength, precipitation, and phenology data from other sources into our own phenology models.**

Figure 2. Clarify that you are showing the forecast for the 6 months beyond February.  Line 518 - could say “forecast for the leaf out of Acer saccharinum in spring 2019.” I suggested above to turn this figure into 3 panels so they can each be referred to in the text. For clarity, consider changing the title of each map.  Currently each says the same thing, “Plant Phenology Forecasts - silver maple”  but it would be more obvious what the differences are among this maps if the large title were changed to say what the small subheading said “Predicted date of leaf out,” and “Anomaly for date of leaf out.”

**We've changed the Figure 2 text to reflect that Feb. 21 is the issue date.  The maps already contain subheading titles for "predicted date","anomaly", and "uncertainty", though we admit the figure resolution was quite low which made them difficult to read. We have increased their resolution so they can be read more easier. Also see the comment above referencing Lines 196 - 208 in regards to Figure 2.**

Figure 3. This figure is very busy. Consider dropping two of the small graphs and be selective about which ones you leave to demonstrate the variation in responses of the model. The axes of these graphs are dates by dates.  They need labels both on the figure and in the caption.

**We've adjusted this figure to only have 4 (instead of 6) timeseries, have added axis titles, and made a more descriptive legend.**

Figure 4. Add the number of taxa covered in this graph to the caption… “for XX species.”  They y axis is unlabeled in the figure.  Please add one. 

**We have added the species count as well as a y-axis**

### Supplement
Line 12: DOY is undefined.  That is jargon that should be defined. Day of year. 

**We've defined DOY here.**

Lines 71-75: There is a change to the writing style here.  Theses lines are written as commands and need to be changed to reflect

**Apologies, this paragraph should be a list and it has been fixed.**
