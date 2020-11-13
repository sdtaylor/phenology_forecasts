Editor comments (Nigel Yoccoz)
MAJOR REVISIONS
Three reviewers have provided very detailed and constructive comments on your paper, emphasizing the relevance of your work, but also pointing out weaknesses. I agree that this is a very nice contribution, and I would like to add a few comments of my own:

While I agree that evaluating the performance of near-term forecasts has recently been emphasized, it has been an important component of adaptive management – see e.g. Nichols et al. (2015) for a very good example. [I have collaborated with Nichols so I am a bit biased, but I think the idea has been around for a while even if the “near-term forecasting aspect was not emphasized as such perhaps.]

When evaluating forecasts, an important aspect might be what the forecasts are used for, and the costs of making different errors. I fully understand that you cannot investigate this fully, but at least a comment is warranted. For example, it might be more costly to forecast budburst or flowering that is too late rather than too early.

You focus on RMSE and coverage to evaluate forecasts, but I was a bit surprised you did not consider bias at all. One reviewer suggested also another criterion. The point is not to assess all kinds of criteria, but to remember that different criteria often lead to different “best methods” (Makridakis 2020).

You do not discuss measurement error, for the data used to fit models and to assess predictions. It may be small compared to the RMSE you show in the different figures, but it would be nice to have your opinion regarding the assessment of forecasts when both the initial data and the data used to assess the forecasts have the same measurement error (or not).

l. 62: giving a R2 without the context is not very helpful – is that the squared correlation between observed and predicted value? How good was the climatological forecast? One may have a high R2 only by having some extreme values that are well predicted etc.

l. 116: you use a simple bootstrap? That is, not taking into account the highly hierarchical nature of the data (i.e. localities*species)?

l. 137: what do you mean by bootstrapped parameter sets?

l. 271-2: You are aware that forecasting based on model ensembles can be based on weights that depend on data configurations, models, etc. (for example in your case you may have weights that change according to the date). This has been in fact standard practice in weather forecasting for quite some time now (see Gneiting and Raftery 2005 for an early presentation).

Gneiting, T., and A. E. Raftery. 2005. Weather forecasting with ensemble methods. Science 310:248-249.

Makridakis, S., and F. Petropoulos. 2020. The M4 competition: Conclusions. International Journal of Forecasting 36:224-227.

Nichols, J. D., F. A. Johnson, B. K. Williams, and G. S. Boomer. 2015. On formally integrating science and policy: walking the walk. Journal of Applied Ecology 52:539-543.


--------------------------------------
# Reviewer 1 
## Basic reporting
Yes mostly other than I think a little more details about the models used is necessary instead of just completely leaving that all to a previously published paper. The authors say that the detailed description of the models is in their 2020 paper. I would like to see some more description of what exactly the models are, specifically that they are growing degree day models with a base temperature of 0C, which I got from the 2020 paper. This would make the paper more of a stand-alone paper. I am a little concerned with only using growing degree days and not cooling degree days for estimating the timing of fall colors and I think this knowledge should be available to the reader of this paper.
## Experimental design
Excellent and impressive.
## Validity of the findings
Findings are valid.
## Comments for the Author
In this manuscript, Taylor and White explain the next advancement of their vegetation phenology forecast system that includes additional sources of uncertainty and their analysis to understand these sources of uncertainty. Overall, I think the paper and design is well thought out and executed. The continental level of their species-specific forecasts is impressive.
There are a couple discussion points that I would like to see further addressed that are important in the interpretation of their results, specifically the major finding that assimilating observed data and using climatic averages for the forecasted section (or just using climatic averages for the whole year) results in smaller errors than using climate forecasts. Additional discussion and potentially analysis to clarify the context would greatly improve it.
To start out with, some more analysis and discussion is needed around how similar the tested year is in terms of phenology (and temperature) to the calibration years. Phenological change in most places is often similar between years, which is why climatic average models typically perform well. The questions and skill often lie in the years that are more extreme. It is difficult to judge how applicable their finding of the skill being higher using climatic averages versus forecasted temperature is without any indication how 2018 compares to the average. Ecological studies are often forced to be heavily dependent on the specific year and study location studied, which is not problematic as long as adequate descriptions are given. Based on what I read, the authors correctly reported their findings for their study year, but some sort of comparison of the study year to the calibration period (even if basic) is necessary. This is becoming more necessary as global climate change is being shown to alter the timing of phenological transitions. The interpretations of the findings is sound, but if the authors decide to not do any additional analysis I do think at least some discussion about how this might not be relevant to all years (especially extreme ones) is needed so the reader does not over-interpret the results.
Secondly, the authors state that the CFSv2 global climate model generally has low predictive ability for temperature. It would be useful to see how the predictive temperatures compared to the actual temperatures in 2018 to see if the poor predictive ability of the forecast product is actually what is impacting method 1’s performance.

Some more specific comments include:
Lines 69-70: I do not necessarily completely agree with the statement that as more time will improve the forecasts especially (1) if the models are really simple and do not represent the process well and (2) given phenology is non-stationary and has been shown to be changing with a changing climate. Please provide a little more justification/clarification for this.

Line 73: what specifically do you mean by “lagged” variables? This is unclear to me. Additionally, by “spring” do you mean phenological spring or calendar spring?

Line 89-90: You have yet to introduce what “The phenology forecast system currently in production” is. It was unclear here that this refers to the authors’ system that is described in a previous paper and not a well-known one (this is not meant to be a judgement on how well-known their forecast system is).

Line 141-142: Not all phenology forecasts need to have dates as the response variable instead of phenological state so I would clarify this as being a consequence of the necessity of simplifying many forecasts to predict dates at large scales because of the computational cost.

Line 265-268: These climatic forecasts would not be as useful in extreme years or in future years that have been affected by a changing climate. This should be discussed in relation to my previous general comments. 

----------------------------------------
# Reviewer 2 (Anonymous)
## Basic reporting
high quality, though see review comments about how a few terms are defined/used.
## Experimental design
no comment
## Validity of the findings
Per general comment #1 below, I am concerned about the interpretation of the coverage statistic and the lack of inclusion of process and observation error. Other than that, I believe the analysis is valid and conclusions well stated.
## Comments for the Author
In this paper Taylor and White look at the impact of driver, model, and parameter uncertainty on the skill of the near-term phenology forecast system that they have previously published on. Overall the paper was well written with good use of previous literature and good figures.

I do have some concerns, which I’ve tried to organize by priority:

1. Lack of inclusion of residual error. The authors note in their Discussion that a future direction would be to account for observation and process error (which together make up the residual error), so they are clearly aware of their importance. What I’m concerned they may be missing is that, in my judgement, their failure to include the residual error in their predictions is causing them to systematically misinterpret their Coverage statistics (e.g. L196). Specifically, they are currently just generating what is technically a confidence interval (uncertainty about the MEAN) not a predictive interval. They are doing a great job in accounting for the uncertainty in parameters, drivers, and model structure in that CI (e.g. by contrast a traditional regression CI just includes parameter uncertainty), but this is still just representing uncertainty about the “expected value” (=mean). As such, we would NOT expect 95% of the data to fall within the 95% CI. What we’re shooting for in coverage is for 95% of the observations to fall within the 95% *predictive interval* (PI). Therefore, the high-level conclusion that coverage is always overconfident is misplaced/overstated. Note, for this particular type of event forecast, I'm not sure observation and process error are easily separable, and I'm fairly confident that your ultimate prediction will be the same whether you partition them or not, so I think it's fine to just include the residual error in the PI, which is a much more straightforward fix.  
[aside: it’s a shame we as a community don’t yet have good language to distinguish different intervals by the uncertainties they contain, other than CI and PI]  

2. Definition of data assimilation (DA): On L46 you define DA to include new information on drivers. In my opinion, this is a significant departure from community norms and results in a title and text that are unclear/confusing. I think calling what you’re doing here DA is going to confuse readers that know what DA is and muddy the water for the portion of the forecasting community that *is* doing DA, because you’re now creating readers who are going to have a harder time understanding what DA actually is. I’d strongly encourage you to use a different term to refer to the different driver scenarios you are evaluating.  


3. Methods sparsity: In general, I found the Methods to be overly reliant on Taylor and White 2020. Not only is this paper not sufficiently detailed to replicate, but I find that it is hard to even follow what was actually done. In particular, four models are referenced without ANY explanation of what these models are or what their assumptions/parameters are. I think you need to add at least some text explaining these models. Similarly, you mention four different phenophases (L107) but it’s unclear which of these are actually being forecast (does the Dec-May period really include forecasts of mature fruit and fall colors?). The Methods also don’t state WHERE this forecast is running (spatial domain), how many species are being considered, or what the sample size is of the validation data. It’s also unclear if the forecast is running for the individual phenology observation locations, or if it’s run on some spatial grid, and if the latter what the grid resolution is. Similarly, since parameter error is being considered it is important to report the time period and sample size of the calibration and the total number of models that were being calibrated.  


4. Unweighted ensemble: The authors use an unweighted ensemble (L115) to account for model structural error, but the phrasing of this statement implies that their previous paper may have weighted the ensemble members. Unless the 4 models being considered had equal skill for all species and phenophases, I’d argue that using an unweighted ensemble misrepresents, and systematically overestimates, the contribution of model structural error to the overall error budget. This is important because, as figure S3 shows, model structure ends up being increasingly important as the forecast progresses and is probably the dominant uncertainty in the last 1/3 to 1/4 of the forecast period. In weighting the model structures, it seems likely that these weights be calculated on a species by phenophase basis.

Smaller errors:
5. Posterior distributions: In a few places (e.g. L132) you refer to your ensemble as a posterior distribution. However, it’s clear that your forecast uses frequentist methods (e.g. bootstrapping) and thus this distribution isn’t a posterior.


6. Forecast horizon: There seems to be a growing consensus that Petchey et al’s “forecast horizon” is actually what most other communities call the “forecast limit” and that the forecast horizon more typically refers to the temporal extent of the model run itself.


7. L288: I think this might be a fragment, rather than a proper sentence.


8. In Fig 4 and S3, the convergence of the climate only forecasts to such narrow estimates makes me wonder if you’re failing to account for the uncertainties in the observed meteorology. I’m not asking for this to be rerun, but if you aren’t including that uncertainty you might mention that in the Methods & Discussion.

I also have a few suggestions that I feel would improve the paper

9. Empirical CDF of phenology events: One thing that made the results hard for me to interpret was that I didn’t know when the events being predicted were actually occurring (except for a small number of examples in a supplement). One simple way to improve that might be to plot the empirical CDF of the phenological event dates (observations not predictions).


10. Phenophase and model faceting: To me, I think it would be really helpful to have at least SOME of the figures (maybe supplement) faceted by the different phenophases being predicted and the different forecast models, since they could differ considerably in their predictability. For example, in Fig 2, I can’t help but wonder if the black and grey lines are doing better for some models and phenophases and worse for others.


11. CRPS: Because your forecasts are probabilistic, in addition to RMSE and coverage you might want to consider using the Continuous Ranked Probability Score, which is a nice composite statistic that accounts for both forecast accuracy and precision (i.e penalizes forecasts both for being ‘wrong’ and for being under/over-confident).


12. Figures 3 and S2: It would be good to say more about the bump in error for the black lines that peaks around Mar 1. Looking at S2 the shift predictions to an earlier date makes me wonder if there was an anomalously warm period in late Feb of the validation year? Ultimately, this seems like something to keep an eye on in the future to see if it is just a quirk of this particular year or something that tends to happen with the Obs+Climatology driver.


13. Parameter uncertainty: Looking at Figure S3 the contribution of parameter uncertainty seems fairly large – larger than I was expecting given what I assume was a fairly large amount of NPN data used in calibration. I was curious if this parameter uncertainty was consistent across forecasts, or if it was being driven by specific groups (e.g. less common species), models, or phenophases.  


14. L275: I like the suggestion of shifting the weight from the climatology at long leads to the observed meteorology at shorter leads. My question is whether you’re proposing that this would need to be done by some sort of calibrated weighting function, or whether you think this would just emerge naturally if you weighted the different forecasts by their precisions? I’m cautiously optimistic that the latter approach would work, especially if the residual error was calibrated correctly and propagated into the weights. Would be nice to add a few more sentences clarifying what exactly you’re proposing.


15. Fig S3: Maybe it's just me, but I found these figures to be easier to understand than Fig 4. Maybe do Fig 4 as a 3 x 2 grid with S2 as the second column? Up to you, just an idea.


16. Fig S2: I was wondering why there weren’t interval estimates the actual forecasts, since you have versions that accounted for parameter and model error. Is this figure depicting the mean of the full ensemble, or just the mean of the Climate Only runs? 

----------------------------------------------------

# Reviewer 3 (Anonymous)
## Basic reporting
I reviewed the manuscript ‘Influence of climate forecasts, data assimilation and uncertainty propagation on the performance of near-term phenology forecast’. The study addresses a very interesting topic that is scarcely evaluated in the scientific literature: the uncertainly associated with climatic data projections and to the model choice in short- and long-term predictions of ecological processes. While I think the methodology is robust (including an exhaustive evaluation of uncertainty propagation), I found the terminology used throughout the manuscript makes reading comprehension difficult. Also, I understand part of the methodology is developed and published elsewhere but the readers of this manuscript would appreciate an additional brief description of some elements of the modelling approach. I believe the manuscript will benefit from some minor additional changes:

Climatic data is used in different parts of the modelling approach used here. The authors refer to it in ways I found confusing. The method 3 (section lines 153-184) that propagates historically observed temperatures to predict near-term phenology is called ‘long- term climate only’ and ‘climatological only’, in Figs. 1 and 2-4, respectively. However, climatological data feeds all models independently of the method and this confuses readers. I would suggest changing the name of the three different methods tested so it intuitively reflects the data used in each case (e.g. Method 3 ‘Long-term historical climate only’ so something similar). Another example in lines 95-96: ‘…can improve forecasts over a climatological average...’: it is unclear to what exactly this climatological average refers to (long-term averaged projections? the ensemble of climatic forecasts?). Also, for example, phases in lines 51-56 are a tongue twister with the word 'forecasts' used too many times. Consider changing the wording to clarify that section. For example, in (line 51) consider changing ‘long-term driver forecasts based on climate scenarios’ by ‘long term data (covering temporal windows > 25years) based on climate projections…’ . This terminological issue has to be clarified and standardized so that the ‘climatological terms’ are used consistently across the manuscript.


## Experimental design
Phenologic event evaluated. While I understand the response variable of the models is the predicted day of the year for a given phenology event, it is unclear (for a non-expert on phenology modeling as myself) whether the four models used in the manuscript relate to a particular phenology event (e.g. flowering) or whether at each point different phenology events were modelled and then values aggregated somehow. Because the manuscript focuses on the uncertainty around the methodological decisions, it loses a bit the context of the ecological process that is being modelled. In my opinion, it is a pity to lose the context of the manuscript. It would be nice for readers to find a brief explanation of the ecological models in the methods of this ms or at least a phrase describing what are the main differences between them (see also my next comment about parameters).

Parameter uncertainty. There is no information about the exact parameters considered in the models so it is hard to interpret how their change might influence estimation uncertainty (as described in lines 50, 116, 137). Is the uncertainty related to the fact that each bootstrap interaction can change the number of parameters in each model? or the parameters themselves? (i.e. the actual values of the parameters?). If the former applies, what was the candidate parameter predictor's set composed of? And why?. If the latter applies, how exactly the parameter values were changed in each bootstrap? This is unclear in the methods and only slightly mentioned in the discussion (lines 251-258). Given that forecasts coverage especially improves when parameter uncertainty is taken into account along with climate and model uncertainty, I think this deserves a more detailed explanation.

Line 118. Data filtering protocols. What do these consist of? (e.g. outlier removal?) Please, explain briefly.

## Other minor comments:

Line 56. Change ‘the potentially chaotic nature…’ by ‘the unpredictable nature’  

Line 82 ‘Climate forecast also involve additional uncertainly in the resulting ecological forecast’ why is this the case? Additional in relation to what exactly? long-term climatic projections? Please clarify.  


## Validity of the findings
No comment 
