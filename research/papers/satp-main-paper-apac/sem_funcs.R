# CircE needs to be installed from GitHub:
library(CircE)

# Ideal angles for circumplex analysis
eq_angles <- c(0, 45, 90, 135, 180, 225, 270, 315)
# Names of the scales for circumplex analysis
scales <- c("PAQ1", "PAQ2", "PAQ3", "PAQ4", "PAQ5", "PAQ6", "PAQ7", "PAQ8")

step_one_test <- function(
    data,
    model_type,
    scales = c("PAQ1", "PAQ2", "PAQ3", "PAQ4", "PAQ5", "PAQ6", "PAQ7", "PAQ8"),
    m = 3) {
  data_paqs <- data[scales] # extract paq columns
  data_paqs <- na.omit(data_paqs) # remove missing data
  data_cor <- cor(data_paqs) # calculate correlation matrix
  n <- dim(data_paqs)[1] # Number of samples

  dimnames(data_cor) <- list(scales, scales) # Name correlation matrix dims

  # option to specify a different m for each model type
  if (length(m) > 1) {
    m_val <- as.integer(m[model_type])
  } else {
    m_val <- m
  }

  if (model_type == "Unconstrained") {
    equal_ang <- FALSE
    equal_com <- FALSE
  } else if (model_type == "Equal comm.") {
    equal_ang <- FALSE
    equal_com <- TRUE

  } else if (model_type == "Equal angles") {
    equal_ang <- TRUE
    equal_com <- FALSE
  } else if (model_type == "Circumplex") {
    equal_ang <- TRUE
    equal_com <- TRUE
  }


  # Input correlation matrix is not positive definite, so
  # Image Factor Analysis (IFA) cannot be used (per CircE docs),
  # Principal Factor Analysis (PFA) is used instead
  res_model <- CircE.BFGS(data_cor,
                          v.names = scales,
                          m = m_val,
                          N = n,
                          start.values = "PFA",
                          equal.ang = equal_ang,
                          equal.com = equal_com,
                          iterlim = 1000,
                          try.refit.BFGS = TRUE)

  # Extract relevant metrics and save
  res_list <- list(
    "model_type" = model_type,
    "n" = n,
    "m" = m_val,
    "chisq" = round(res_model$chisq, 2),
    "df" = res_model$d,
    "chi.p.val" = round(1 - pchisq(res_model$chisq, df = res_model$d), 4),
    "cfi" = round(res_model$CFI, 2),
    "gfi" = round(res_model$GFI, 2),
    "agfi" = round(res_model$AGFI, 2),
    "srmr" = round(res_model$SRMR, 2),
    "mcsc" = round(res_model$MCSC, 2),
    "rmsea" = round(res_model$RMSEA, 2),
    "rmsea.l" = round(res_model$RMSEA.L, 2),
    "rmsea.u" = round(res_model$RMSEA.U, 2),
    "paq1.ang" = res_model$polar.angles["PAQ1", "estimates"],
    "paq2.ang" = res_model$polar.angles["PAQ2", "estimates"],
    "paq3.ang" = res_model$polar.angles["PAQ3", "estimates"],
    "paq4.ang" = res_model$polar.angles["PAQ4", "estimates"],
    "paq5.ang" = res_model$polar.angles["PAQ5", "estimates"],
    "paq6.ang" = res_model$polar.angles["PAQ6", "estimates"],
    "paq7.ang" = res_model$polar.angles["PAQ7", "estimates"],
    "paq8.ang" = res_model$polar.angles["PAQ8", "estimates"],
    "gdiff" = gdiff(res_model$polar.angles$estimates)
  )

  res <- list(
    "res_model" = res_model,
    "res_list" = res_list
  )
}


# Add step one model results to results table
add_to_res_table <- function(res_table, res_list, datasource, language) {
  model_type <- res_list$model_type

  res_table[model_type, "Dataset"] <- datasource
  res_table[model_type, "Language"] <- language
  res_table[model_type, "Model Type"] <- model_type
  res_table[model_type, "n"] <- res_list$n
  res_table[model_type, "m"] <- res_list$m

  res_table[model_type, "ChiSq"] <- res_list$chisq
  res_table[model_type, "df"] <- res_list$df
  res_table[model_type, "p"] <- res_list$chi.p.val
  res_table[model_type, "CFI"] <- res_list$cfi
  res_table[model_type, "GFI"] <- res_list$gfi
  res_table[model_type, "AGFI"] <- res_list$agfi
  res_table[model_type, "SRMR"] <- res_list$srmr
  res_table[model_type, "MCSC"] <- res_list$mcsc
  res_table[model_type, "RMSEA"] <- res_list$rmsea
  res_table[model_type, "RMSEA.L"] <- res_list$rmsea.u
  res_table[model_type, "RMSEA.U"] <- res_list$rmsea.l

  if (model_type == "Unconstrained" || model_type == "Equal comm.") {
    res_table[model_type, "PAQ1"] <- as.numeric(res_list$paq1.ang)
    res_table[model_type, "PAQ2"] <- as.numeric(res_list$paq2.ang)
    res_table[model_type, "PAQ3"] <- as.numeric(res_list$paq3.ang)
    res_table[model_type, "PAQ4"] <- as.numeric(res_list$paq4.ang)
    res_table[model_type, "PAQ5"] <- as.numeric(res_list$paq5.ang)
    res_table[model_type, "PAQ6"] <- as.numeric(res_list$paq6.ang)
    res_table[model_type, "PAQ7"] <- as.numeric(res_list$paq7.ang)
    res_table[model_type, "PAQ8"] <- as.numeric(res_list$paq8.ang)
    res_table[model_type, "GDIFF"] <- res_list$gdiff
  }

  res_table
}

# Run all four models for a language and compile into single table
run_all_models <- function(data, datasource, language, m) {
  # Extract the data for the language
  lang_data <- data[data$Language == language, ]

  # Create empty table to store results
  form_res <- matrix(ncol = 25, nrow = 4)
  colnames(form_res) <- c("Dataset", "Language", "Model Type", "n", "m",
                          "ChiSq", "df", "p", "CFI", "GFI", "AGFI",
                          "SRMR", "MCSC", "RMSEA", "RMSEA.L", "RMSEA.U",
                          "PAQ1", "PAQ2", "PAQ3", "PAQ4",
                          "PAQ5", "PAQ6", "PAQ7", "PAQ8",
                          "GDIFF")
  rownames(form_res) <- c("Unconstrained", "Equal comm.",
                          "Equal angles",  "Circumplex")

  # Convert to table
  res_table <- as.table(form_res)

  # Create empty list to store results
  res_list <- list("Data source" = datasource, "Language" = language)

  # Run all four models
  for (model in c("Unconstrained", "Equal comm.",
                  "Equal angles", "Circumplex")
  ) {
    # Run model
    model_res <- step_one_test(lang_data, model, m = m)
    # Add results to table
    res_table <- add_to_res_table(res_table,
                                  model_res$res_list,
                                  datasource,
                                  language)
    # Add results to list
    res_list[model] <- list(model_res$res_model)
  }

  # Return results
  all_res <- list("res_table" = res_table, "res_list" = res_list)
}

gdiff <- function(obs_angles) {
  id_angles <- c(0, 45, 90, 135, 180, 225, 270, 315)
  rev_angles <- c(0, 315, 270, 225, 180, 135, 90, 45)

  if (sum(obs_angles[1:3]) > 300) {
    ideal <- rev_angles
  } else{
    ideal <- id_angles
  }

  s <- 0
  for (i in seq_along(obs_angles)) {
    s <- s + (obs_angles[i] - ideal[i])^2
  }

  g <- sqrt((1 / 8) * s)
  round(g, 2)
}