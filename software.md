---
title: Software
echo: false
section-divs: false
keep-md: true
---


## `tidyhte` {#tidyhte}
tidyhte provides tidy semantics for estimation of heterogeneous treatment effects through the use of Kennedy's (n.d.) doubly-robust learner.  
The goal of tidyhte is to use a sort of “recipe” design. This should (hopefully) make it extremely easy to scale an analysis of HTE from the common single-outcome / single-moderator case to many outcomes and many moderators. The configuration of tidyhte should make it extremely easy to perform the same analysis across many outcomes and for a wide-array of moderators. It’s written to be fairly easy to extend to different models and to add additional diagnostics and ways to output information from a set of HTE estimates.


```{=html}
<a class="btn btn-outline-dark btn-sm", href="https://ddimmery.github.io/tidyhte/">
        <i class="bi bi-info" role='img' aria-label='Website'></i>
        Website
    </a> <a class="btn btn-outline-dark btn-sm", href="https://github.com/ddimmery/tidyhte">
        <i class="bi bi-github" role='img' aria-label='Github'></i>
        Github
    </a>
```

## `regweight` {#regweight}
The goal of regweight is to make it easy to diagnose a model using Aronow and Samii (2015) regression weights.  
In short, these weights show which observations are most influential for determining the observed value of a coefficient in a linear regression. If the linear regression is aiming to estimate causal effects, this implies that the OLS estimand may differ from the average treatment effect. These linear regression weights provide, in some sense, the most precise estimate available given a conditioning set (and a linear model). These weights are in expectation the conditional variance of the variable of interest (given the other covariates in the model).


```{=html}
<a class="btn btn-outline-dark btn-sm", href="https://ddimmery.github.io/regweight/">
        <i class="bi bi-info" role='img' aria-label='Website'></i>
        Website
    </a> <a class="btn btn-outline-dark btn-sm", href="https://github.com/ddimmery/regweight">
        <i class="bi bi-github" role='img' aria-label='Github'></i>
        Github
    </a> <a class="btn btn-outline-dark btn-sm", href="https://cran.r-project.org/package=regweight">
        <i class="bi bi-box-seam" role='img' aria-label='Package'></i>
        Package
    </a>
```

## `rdd` {#rdd}
**Outdated!** Users should switch to [actively maintained and updated RD tools](https://rdpackages.github.io/).  
Provides the tools to undertake estimation in Regression Discontinuity Designs. Both sharp and fuzzy designs are supported. Estimation is accomplished using local linear regression. A provided function will utilize Imbens-Kalyanaraman optimal bandwidth calculation. A function is also included to test the assumption of no-sorting effects.


```{=html}
<a class="btn btn-outline-dark btn-sm", href="https://github.com/ddimmery/rdd">
        <i class="bi bi-github" role='img' aria-label='Github'></i>
        Github
    </a> <a class="btn btn-outline-dark btn-sm", href="https://cran.r-project.org/package=rdd">
        <i class="bi bi-box-seam" role='img' aria-label='Package'></i>
        Package
    </a>
```
