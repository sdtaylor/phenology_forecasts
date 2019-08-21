## Reviewer: 1

Comments to the Author

This manuscript describes the operationalization of an automative plant phenology forecasting system for 78 species across the continental U.S. The authors clearly document a reproducible pipeline for implementing their forecasts, allowing other developers to leverage off their work. This work is timely given the scientific community’s increased interest in ecological forecasting, and it will make a valuable contribution to the literature. 

Major concerns.
-My only major critique is that as a reader who isn’t an expert in phenology forecasting, I was left unsure of the major improvements this system has over other existing systems. In the introduction the authors mention that most phenology forecasts focus on spring indices as opposed to phenophase level forecasts. Does this system also have the finest spatial scale? The most number of species? The large spatial coverage? Would be good to point to the outputs of other phenology forecasts and clearly describe the improvements made in the present study. 

Abstract.

Line 11. Would it be possible to include a more specific definition of phenology for readers that are unfamiliar with the term? Something like: “Phenology – the timing of cyclical and seasonal natural phenomena such as flowering and leaf out - …”

Line 12-13. Suggest: “…with impacts on human activities like environmental management, tourism, and agriculture.”

Line 15. What is mean by broad scale? A large volume of data? Broad spatial coverage? Broad temporal coverage?

Line 17. Volume should be plural.

Introduction.

Line 28. Again, here would be good to provide a more in-depth description of phenology.

Line 37. Would be good to conclude this paragraph with a problem statement similar to the one in the abstract. Something along the lines of: “However, due to the challenges of automatically integrating, predicting, and disseminating large volumes of data, there are limited examples of applied phenology forecast systems.”

Line 42. Perhaps this is discussed elsewhere in the manuscript, but would be interesting to include a discussion of the timing of plant response to changes in the weather. For example, how long does a temperature spike need to persist to initiate a leaf-out event? If we have one warm day, is that long enough to trigger a change in phenology, or do warmer temperatures need to persist for days or weeks? Is the plant response immediate, or is there a time lag? And how does this interplay with climatological triggers? Presumable plants are also responding to non-weather drivers, such as changing light availability. 

Line 49. Near-term or near term. Select one for consistency throughout (abstract uses near-term).

Line 51. Please include an example of an integrate spring index. I’m assuming it’s aggregated across multiple species and multiple phenophases?

Line 57-60. Would be good to be more explicit about the types of scales being discussed. Line 59 makes it sound like this is a discussion of spatial scale. But I assume this present analysis is also more challenging given that it includes a large number of species and multiple types of phenologic events, and as is stated in the following sentences, the high spatial resolution.

Lines 50-69. Suggest restructuring this paragraph to make it easier to grasp its purpose, which I believe is to demonstrate the limits of current phenology forecasts, and why to date we haven’t seen a phenology forecast at the scale of the one in the manuscript. Perhaps something like: “For applied use in planning exercises, plant phenology forecasts are most informative when produced at species- and phenophase-levels, over large spatial scales, and at high spatial resolutions. However forecasting at this level of detail is challenging due to the need for advanced computation tools to build and maintain automative forecasting systems.” And then go on to explain your points on integrated spring indices, regional forecasts, downscaled seasonal climate forecasts. 

Line 77. Would it be accurate to say “automating the pipeline to update forecasts with a sub-weekly frequency”? In my work this step would be producing a new forecast for days further in the future, e.g. 6 months + 1 day, 6 months + 2 days, etc. But I believe your system is updating/improving the same forecast for a specific phenophase event as more data comes in. This is a subtle distinction, but I think helpful for readers to grasp the structure of your system.

Methods

Line 92. Suggest being specific in the usage of scale. Here it refers to spatial scale.

Line 93. What range? The prediction range (the continental US) or the species specific range?

Lines 94-96. Over what time range?

Line 99. What phenophases did you select for modeling?

Line 106. What does daily mean temperature refer to? The mean temperature in a 24 hour period? A climatological daily mean?

Line 107. What is the PRISM dataset? Is it modeled? Remote sensing data? Some integrated product?

Line 108-109. Is temperature time-matched to the observations? E.g. for a given record, was the temperature at the time and place of the record used a predictor?

Line 110. Ensembles also help remove model-specific biases.

Line 120-121. Remind the reader how much of each you are working with, e.g. 78 species, four models, xx# phenophases.

Line 131. What are accumulated growing degree days? Perhaps specify in the phenology modeling section.

Line 172. Unsure what a five member ensemble is.

Line 175. What is the range of the time dimension? Now to now + 9 months (the projected period of the CFSv2 forecasts?)

Line 180. Where does information on range come from? Published literature? The extent of the species specific observations?

Line 187-189. Suggest editing: “The members of the climate ensemble each produce a different temperature forecast due to differences in initial conditions.”

Line 190. Five

Line 193. This is really cool. And a really valuable component of the system.

Line 196. Here or elsewhere in the paragraph remind readers of the website URL.

Line 196-197. Here and elsewhere in the methods select one type of voice. “We built a website” vs “a website was built”. 

Line 210. And the building of the downscaling model. Good to specific that you are referencing both the species/phenotype specific models and the downscaling model.

Line 211. Con job. No apostrophe. 

Line 212. “The cron job first runs a script that acquires the newest climate observations...” If someone is reading this paper to learn how to build their own forecasting system, it will help them to have an understanding of how your code block is organized by scripts. Or is everything in one master script? Also what’s the timing of the cron job – first thing in the morning? 

Line 229. Specify that these are R packages.

Discussion

Line 280. “…entry barrier of operationalizing ecological models for decision making…”

Lines 272-285. Hard to understand the main message of this paragraph.  Suggest maintaining first sentence, and then as a second sentence something like: “To facilitate the development of ecological forecasts, we need xxxxxx (applied examples, discussion of the development methodologies, standardized models, software packages, etc).” And then use the remainder of the paragraph to expand on each of the components.

Lines 291-292. How generalizable is your code? Give the reader an indication of how broadly it could be used. Other taxa? Other climate models? Marine forecasts?

Line 292. Automatically

Line 300. Where does 190 come from? 78 species x 4 phenologies = 312.

Line 301. Four different phenology models -> are these the four models in the ensemble?

Line 317. R shiny applications are one avenue for developing interactive maps. Here is a particularly impressive one: https://ctmm.shinyapps.io/ctmmweb/ . 

Line 356-358. This is an important point that I think could be stated a little more directly. While there are many published examples of species distribution models, it’s much harder to find published examples of system operationalization, making it challenging to find templates to follow. Operationalization/implementation is a key component of producing applied tools, and it’s important that pipelines are documented in the literature. Also could stress here that it’s important to make code blocks public so that other developers can leverage them.

Lines 364-366. You’ve already thoroughly explored areas of improvement, and I think it sells your system short to repeat here. Suggest instead focusing on what makes this system novel, e.g. multi-species, unaggregated phenotypes, large spatial coverage, fine spatial resolution, etc. Conclude with what you’ve done well, not what you could have done better. 

## Reviewer: 2
Comments to the Author

Taylor and White present a novel predictive model for flowering time in the USA.  In this paper, they successfully integrate phenological data collected by in-situ observers in the National Phenology Network and climate data to make predictions about multiple phenophases for 78 species six months in advance.  The authors have not only created novel and useful methods that apply to a wide range of ecological applications, but they have made a novel contribution to our understanding of phenological changes. I am optimistic that further development of these methods will enable excellent research across many realms of ecology. 

I  am recommending that the manuscript “Automated data-intensive forecasting of plant phenology throughout the United States” by Taylor and White to be accepted with minor revisions.

The authors have used free and open source tools to build a automated system to forecast phenology at continental scales and provide the data outputs to the public. The authors present a detailed report of their forecasting pipeline, which other users will find informative. They report how to fit the phenological models, acquire and appropriately sample the climate data, make predictions, and serve those predictions to public and well as serving the model code via github. 

The dataset and tools they have created are capable of answering many more interesting questions in ecology.  For example, do most species respond to temperature in the same direction and magnitude?  How variable are species responses?  Are certain phenophases more sensitive to temperature shifts? Does this vary by species?

This paper is well written and the language is astonishingly clear for a paper that focuses on ecological modeling.  Well done. I have a few minor suggestions that will clarify certain parts of the manuscript.

Line 44: For someone unfamiliar with modeling lingo, “operationalization” isn’t clear.

Line 46: Be explicit that the outer predictive range of this paper is 6 months. Here the authors say “this time horizon” and elsewhere “near-term,” without really clarifying what the time horizon is. 

Line 51: “integrated spring indices” is unclear and would be better if explained a bit more in the text. 

Line 70: drop the words “near term” Unnecessary jargon.

Phenological Modeling
Line 100: explain what “Individual Phenometrics” are.
Lines 100-107: This section contributes to a little bit of confusion regarding dataset time frames.  Here the authors say that they extracted NPN data from 2009-2017. But then the authors state that only records with at least 30 observations were included.  Since some species have a large range, and the time scale spans 8 years, are these 30 observations spanning both time and space.  That seems sparse. If that is not the meaning of lines 105-106 please clarify. 
Is the PRISM data spanning the same time period? 

Line 121: How many phenophases?  This is reported in the tables, but it should be added in the text. 

Line 125: Should json be JSON?

Line 131: Define accumulated growing degree days.

Lines 163-166: “perform operations” and “this type of operation” are largely unexplained in this section.  It’s not abundantly clear what is happening here. 

Line 200: The maps show the predicted event for what time in the future?  Is it always 6 months out or can you specify the forecast?  Specify the “when” here.

Line 203: I think a word is missing making this sentence read poorly.

Lines 196 - 208: I think this dissemination section could be strengthened if you turned figure 2 into three discrete panels; A, B, and C.  Then you could reference each map in figure 2 separately when discussing them in this section.  I thought the caption on Fig. 2 was weak and making this change will also correct that. It was not very clear what the different maps were showing from reading only the figure caption. 

Lines 208: Please clarify where the “long term, spatially corrected average date of he phenological events” is coming from.  It is not clear if this is the phenological model made from the NPN data from 2009-2017.  

Evaluation section lines 239-249: I think the first paragraph here needs more clarity.   The authors need to clearly state “We used 2019 data to check the accuracy of our predictions.” This is the point of this section but it’s only alluded to in fancy sentences that obscure the point. 
Was all data from NPN in the time range downloaded of only those pertaining to the taxa in your predictive model? If they are different, is that justified and meaningful?

Line 328: “it’s” should be “its”

Line 361: It might be useful to say if the user can access the metadata behind each forecast.

At some point in the discussion the authors should address if future models will incorporate more than temperature. 

Figure 2. Clarify that you are showing the forecast for the 6 months beyond February.  Line 518 - could say “forecast for the leaf out of Acer saccharinum in spring 2019.” I suggested above to turn this figure into 3 panels so they can each be referred to in the text. For clarity, consider changing the title of each map.  Currently each says the same thing, “Plant Phenology Forecasts - silver maple”  but it would be more obvious what the differences are among this maps if the large title were changed to say what the small subheading said “Predicted date of leaf out,” and “Anomaly for date of leaf out.”

Figure 3. This figure is very busy. Consider dropping two of the small graphs and be selective about which ones you leave to demonstrate the variation in responses of the model. The axes of these graphs are dates by dates.  They need labels both on the figure and in the caption.

Figure 4. Add the number of taxa covered in this graph to the caption… “for XX species.”  They y axis is unlabeled in the figure.  Please add one. 

Supplement
Line 12: DOY is undefined.  That is jargon that should be defined. Day of year. 

Lines 71-75: There is a change to the writing style here.  Theses lines are written as commands and need to be changed to reflect