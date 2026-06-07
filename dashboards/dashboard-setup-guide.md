# CloudWatch Dashboard Setup Guide

Complete JSON definitions for all four CloudWatch dashboards used in the Intelligent House Price Prediction System. Each dashboard can be created directly in the AWS CloudWatch console by navigating to **Dashboards → Create Dashboard** and pasting the corresponding JSON source.

---

## Table of Contents

- [1. RealTimeSpikeMonitoring](#1-realtimespikemonitoring)
- [2. Cost_Savings_Dashboard](#2-cost_savings_dashboard)
- [3. ML_Dashboard](#3-ml_dashboard)
- [4. HousePriceMonitoring](#4-housepricemonitoring)
- [Setup Instructions](#setup-instructions)

---

## 1. RealTimeSpikeMonitoring

Monitors real-time queue behavior, threshold response times, load classification, and cost savings. This dashboard is the primary operational view for observing how the system reacts to traffic spikes.

**Widgets:**
- **Queue Depth** — SQS `ApproximateNumberOfMessagesVisible` showing message backlog over time
- **Threshold Response Time** — Tracks T1, T2, and T3 threshold values as they are dynamically adjusted
- **Load Mode** — Numerical representation of the current traffic classification (1=LOW, 2=MEDIUM, 3=HIGH, 4=SPIKE)
- **Cost Savings (Scaled)** — Scaled cost savings metric for real-time cost efficiency monitoring

```json
{
  "widgets": [
    {
      "height": 6,
      "width": 12,
      "y": 0,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "AWS/SQS",
            "ApproximateNumberOfMessagesVisible",
            "QueueName",
            "property-stream-queue",
            {
              "stat": "Maximum",
              "period": 60,
              "label": "Queue Depth",
              "color": "#1f77b4"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "📊 SQS Queue Depth (Real-Time)",
        "period": 60,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Messages"
          }
        },
        "annotations": {
          "horizontal": [
            {
              "label": "T1 Threshold (LOW→MEDIUM)",
              "value": 3,
              "color": "#2ca02c"
            },
            {
              "label": "T2 Threshold (MEDIUM→HIGH)",
              "value": 14,
              "color": "#ff7f0e"
            },
            {
              "label": "T3 Threshold (HIGH→SPIKE)",
              "value": 39,
              "color": "#d62728"
            }
          ]
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 0,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Threshold_T1",
            {
              "stat": "Average",
              "period": 120,
              "label": "T1 (LOW→MEDIUM)",
              "color": "#2ca02c"
            }
          ],
          [
            "Custom/HousePriceML",
            "Threshold_T2",
            {
              "stat": "Average",
              "period": 120,
              "label": "T2 (MEDIUM→HIGH)",
              "color": "#ff7f0e"
            }
          ],
          [
            "Custom/HousePriceML",
            "Threshold_T3",
            {
              "stat": "Average",
              "period": 120,
              "label": "T3 (HIGH→SPIKE)",
              "color": "#d62728"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🎯 Threshold Response Time (Dynamic T1, T2, T3)",
        "period": 120,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Threshold Value"
          }
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 6,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Load_Mode_Number",
            {
              "stat": "Average",
              "period": 60,
              "label": "Load Mode (1=LOW, 2=MED, 3=HIGH, 4=SPIKE)",
              "color": "#9467bd"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🚦 Current Load Mode Classification",
        "period": 60,
        "yAxis": {
          "left": {
            "min": 0,
            "max": 5,
            "label": "Mode"
          }
        },
        "annotations": {
          "horizontal": [
            {
              "label": "LOW",
              "value": 1,
              "color": "#2ca02c"
            },
            {
              "label": "MEDIUM",
              "value": 2,
              "color": "#ff7f0e"
            },
            {
              "label": "HIGH",
              "value": 3,
              "color": "#d62728"
            },
            {
              "label": "SPIKE",
              "value": 4,
              "color": "#8b0000"
            }
          ]
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 6,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Cost_Savings_Scaled",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Cost Savings (Scaled ×10⁶)",
              "color": "#17becf"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "💰 Real-Time Cost Savings",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Savings (Scaled)"
          }
        }
      }
    }
  ]
}
```

---

## 2. Cost_Savings_Dashboard

The proof dashboard — demonstrates the 98.5% reduction in Lambda invocations and 90% cost savings with gauges, comparisons, and batch efficiency metrics.

**Widgets:**
- **Cost Savings Gauge** — Single-value gauge showing cumulative cost savings (0–100 scale)
- **98.5% Fewer Lambda Invocations** — Side-by-side comparison of our invocations vs traditional (1-per-record) invocations
- **Records per Invocation** — Tracks how many records are processed per Lambda invocation over time
- **Invocation Reduction Percentage Gauge** — Gauge showing the percentage reduction in invocations
- **Batch Efficiency** — Compares actual batch size vs target batch size and shows overall batch efficiency percentage

```json
{
  "widgets": [
    {
      "height": 6,
      "width": 6,
      "y": 0,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "gauge",
        "metrics": [
          [
            "Custom/HousePriceML",
            "Cost_Savings_Scaled",
            {
              "stat": "Sum",
              "period": 3600,
              "label": "Cost Savings",
              "color": "#2ca02c"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "💰 Cost Savings (0–100)",
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100
          }
        },
        "period": 3600,
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 18,
      "y": 0,
      "x": 6,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Total_Batches_Processed",
            {
              "stat": "Maximum",
              "period": 300,
              "label": "Our System (Batched Invocations)",
              "color": "#2ca02c"
            }
          ],
          [
            "Custom/HousePriceML",
            "Total_Records_Processed",
            {
              "stat": "Maximum",
              "period": 300,
              "label": "Traditional System (1 Invocation per Record)",
              "color": "#d62728"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🔻 98.5% Fewer Lambda Invocations — Our System vs Traditional",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Invocations / Records"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 6,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Records_Per_Batch",
            {
              "stat": "Average",
              "period": 300,
              "label": "Records per Invocation",
              "color": "#1f77b4"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "📦 Records per Lambda Invocation (Target: 57+)",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Records"
          }
        },
        "annotations": {
          "horizontal": [
            {
              "label": "Traditional (1 record/invocation)",
              "value": 1,
              "color": "#d62728",
              "fill": "below"
            },
            {
              "label": "Target (57 records/invocation)",
              "value": 57,
              "color": "#2ca02c"
            }
          ]
        }
      }
    },
    {
      "height": 6,
      "width": 6,
      "y": 6,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "gauge",
        "metrics": [
          [
            "Custom/HousePriceML",
            "Invocation_Reduction_Percentage",
            {
              "stat": "Average",
              "period": 3600,
              "label": "Invocation Reduction %",
              "color": "#1f77b4"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🎯 Invocation Reduction Percentage",
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100
          }
        },
        "period": 3600,
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 6,
      "y": 6,
      "x": 18,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Batch_Efficiency_Percentage",
            {
              "stat": "Average",
              "period": 300,
              "label": "Batch Efficiency %",
              "color": "#2ca02c"
            }
          ],
          [
            "Custom/HousePriceML",
            "Actual_Batch_Size",
            {
              "stat": "Average",
              "period": 300,
              "label": "Actual Batch Size",
              "color": "#1f77b4",
              "yAxis": "right"
            }
          ],
          [
            "Custom/HousePriceML",
            "Target_Batch_Size",
            {
              "stat": "Average",
              "period": 300,
              "label": "Target Batch Size",
              "color": "#ff7f0e",
              "yAxis": "right"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "⚙️ Batch Efficiency (Actual vs Target)",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100,
            "label": "Efficiency %"
          },
          "right": {
            "min": 0,
            "label": "Batch Size"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    }
  ]
}
```

---

## 3. ML_Dashboard

Monitors the machine learning pipeline — model accuracy, prediction volume, and price distribution across prediction ranges.

**Widgets:**
- **Model Accuracy** — Tracks the scikit-learn model accuracy percentage over time (0–100%)
- **Records Processed** — Running count of total records processed by the ML engine
- **Prediction Distribution** — Stacked area chart showing predictions broken into three price ranges: Under ₹5M, ₹5M–₹10M, and Over ₹10M

```json
{
  "widgets": [
    {
      "height": 6,
      "width": 12,
      "y": 0,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Model_Accuracy",
            {
              "stat": "Average",
              "period": 300,
              "label": "Model Accuracy (%)",
              "color": "#2ca02c"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🎯 ML Model Accuracy (Percent)",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100,
            "label": "Accuracy %"
          }
        },
        "annotations": {
          "horizontal": [
            {
              "label": "Random Forest Baseline (72%)",
              "value": 72,
              "color": "#ff7f0e"
            },
            {
              "label": "Linear Regression Baseline (61%)",
              "value": 61,
              "color": "#d62728"
            }
          ]
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 0,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Records_Processed",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Records Processed (per interval)",
              "color": "#1f77b4"
            }
          ],
          [
            "Custom/HousePriceML",
            "Total_Records_Processed",
            {
              "stat": "Maximum",
              "period": 300,
              "label": "Cumulative Records Processed",
              "color": "#9467bd",
              "yAxis": "right"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "📈 Records Processed",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Records (Interval)"
          },
          "right": {
            "min": 0,
            "label": "Records (Cumulative)"
          }
        }
      }
    },
    {
      "height": 6,
      "width": 24,
      "y": 6,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": true,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Under_5M",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Under ₹5M",
              "color": "#2ca02c"
            }
          ],
          [
            "Custom/HousePriceML",
            "5M_10M",
            {
              "stat": "Sum",
              "period": 300,
              "label": "₹5M – ₹10M",
              "color": "#ff7f0e"
            }
          ],
          [
            "Custom/HousePriceML",
            "Over_10M",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Over ₹10M",
              "color": "#d62728"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🏠 Prediction Price Distribution",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Number of Predictions"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 12,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Mean_Absolute_Error",
            {
              "stat": "Average",
              "period": 300,
              "label": "Mean Absolute Error (₹)",
              "color": "#d62728"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "📉 Mean Absolute Error",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Error (₹)"
          }
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 12,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Current_Model_Accuracy",
            {
              "stat": "Average",
              "period": 300,
              "label": "Current Active Model",
              "color": "#2ca02c"
            }
          ],
          [
            "Custom/HousePriceML",
            "Linear_Regression_Baseline_Comparison",
            {
              "stat": "Average",
              "period": 300,
              "label": "Linear Regression",
              "color": "#1f77b4"
            }
          ],
          [
            "Custom/HousePriceML",
            "Random_Forest_Advanced_Comparison",
            {
              "stat": "Average",
              "period": 300,
              "label": "Random Forest",
              "color": "#ff7f0e"
            }
          ],
          [
            "Custom/HousePriceML",
            "Gradient_Boosting_Premium_Comparison",
            {
              "stat": "Average",
              "period": 300,
              "label": "Gradient Boosting",
              "color": "#9467bd"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🤖 Algorithm Comparison",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100,
            "label": "Accuracy %"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    }
  ]
}
```

---

## 4. HousePriceMonitoring

End-to-end operational health dashboard covering SQS backlog, Lambda throughput, cost comparison, and DynamoDB capacity.

**Widgets:**
- **SQS Message Backlog** — Visible, not-visible, and in-flight message counts for the property queue
- **Lambda Invocations Per Minute** — Per-function invocation rates for all four Lambda functions
- **Cost Comparison** — Side-by-side time series of traditional cost estimate vs our optimized cost estimate
- **DynamoDB Capacity Usage** — Read and write capacity consumption for the `ProcessedResults` and `BatchMetadata` tables

```json
{
  "widgets": [
    {
      "height": 6,
      "width": 12,
      "y": 0,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": true,
        "metrics": [
          [
            "AWS/SQS",
            "ApproximateNumberOfMessagesVisible",
            "QueueName",
            "property-stream-queue",
            {
              "stat": "Average",
              "period": 60,
              "label": "Messages Visible (Waiting)",
              "color": "#d62728"
            }
          ],
          [
            "AWS/SQS",
            "ApproximateNumberOfMessagesNotVisible",
            "QueueName",
            "property-stream-queue",
            {
              "stat": "Average",
              "period": 60,
              "label": "Messages Not Visible (In-Flight)",
              "color": "#ff7f0e"
            }
          ],
          [
            "AWS/SQS",
            "NumberOfMessagesSent",
            "QueueName",
            "property-stream-queue",
            {
              "stat": "Sum",
              "period": 60,
              "label": "Messages Sent (Inflow)",
              "color": "#2ca02c"
            }
          ],
          [
            "AWS/SQS",
            "NumberOfMessagesReceived",
            "QueueName",
            "property-stream-queue",
            {
              "stat": "Sum",
              "period": 60,
              "label": "Messages Received (Outflow)",
              "color": "#1f77b4"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "📬 SQS Message Backlog",
        "period": 60,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Messages"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 0,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "AWS/Lambda",
            "Invocations",
            "FunctionName",
            "production-data-generator",
            {
              "stat": "Sum",
              "period": 60,
              "label": "Data Generator",
              "color": "#1f77b4"
            }
          ],
          [
            "AWS/Lambda",
            "Invocations",
            "FunctionName",
            "production-property-collector",
            {
              "stat": "Sum",
              "period": 60,
              "label": "Property Collector",
              "color": "#ff7f0e"
            }
          ],
          [
            "AWS/Lambda",
            "Invocations",
            "FunctionName",
            "production-property-processor",
            {
              "stat": "Sum",
              "period": 60,
              "label": "Property Processor",
              "color": "#2ca02c"
            }
          ],
          [
            "AWS/Lambda",
            "Invocations",
            "FunctionName",
            "production-threshold-optimizer",
            {
              "stat": "Sum",
              "period": 60,
              "label": "Threshold Optimizer",
              "color": "#d62728"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "⚡ Lambda Invocations Per Minute",
        "period": 60,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Invocations"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 6,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "Custom/HousePriceML",
            "Traditional_Cost_Estimate",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Traditional System Cost (Scaled ×10⁶)",
              "color": "#d62728"
            }
          ],
          [
            "Custom/HousePriceML",
            "Our_Cost_Estimate",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Our System Cost (Scaled ×10⁶)",
              "color": "#2ca02c"
            }
          ],
          [
            "Custom/HousePriceML",
            "Baseline_Cost_Scaled",
            {
              "stat": "Maximum",
              "period": 300,
              "label": "Baseline Cost (Cumulative)",
              "color": "#ff7f0e",
              "yAxis": "right"
            }
          ],
          [
            "Custom/HousePriceML",
            "Optimized_Cost_Scaled",
            {
              "stat": "Maximum",
              "period": 300,
              "label": "Optimized Cost (Cumulative)",
              "color": "#17becf",
              "yAxis": "right"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "💵 Cost Comparison — Traditional vs Our System",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Cost per Interval (Scaled)"
          },
          "right": {
            "min": 0,
            "label": "Cumulative Cost (Scaled)"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 6,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "AWS/DynamoDB",
            "ConsumedReadCapacityUnits",
            "TableName",
            "ProcessedResults",
            {
              "stat": "Sum",
              "period": 300,
              "label": "ProcessedResults — Read",
              "color": "#1f77b4"
            }
          ],
          [
            "AWS/DynamoDB",
            "ConsumedWriteCapacityUnits",
            "TableName",
            "ProcessedResults",
            {
              "stat": "Sum",
              "period": 300,
              "label": "ProcessedResults — Write",
              "color": "#ff7f0e"
            }
          ],
          [
            "AWS/DynamoDB",
            "ConsumedReadCapacityUnits",
            "TableName",
            "BatchMetadata",
            {
              "stat": "Sum",
              "period": 300,
              "label": "BatchMetadata — Read",
              "color": "#2ca02c"
            }
          ],
          [
            "AWS/DynamoDB",
            "ConsumedWriteCapacityUnits",
            "TableName",
            "BatchMetadata",
            {
              "stat": "Sum",
              "period": 300,
              "label": "BatchMetadata — Write",
              "color": "#d62728"
            }
          ],
          [
            "AWS/DynamoDB",
            "ConsumedReadCapacityUnits",
            "TableName",
            "OptimizationHistory",
            {
              "stat": "Sum",
              "period": 300,
              "label": "OptimizationHistory — Read",
              "color": "#9467bd"
            }
          ],
          [
            "AWS/DynamoDB",
            "ConsumedWriteCapacityUnits",
            "TableName",
            "OptimizationHistory",
            {
              "stat": "Sum",
              "period": 300,
              "label": "OptimizationHistory — Write",
              "color": "#8c564b"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🗄️ DynamoDB Capacity Usage",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Capacity Units"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 12,
      "x": 0,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "AWS/Lambda",
            "Duration",
            "FunctionName",
            "production-property-processor",
            {
              "stat": "Average",
              "period": 60,
              "label": "Processor Avg Duration",
              "color": "#2ca02c"
            }
          ],
          [
            "AWS/Lambda",
            "Duration",
            "FunctionName",
            "production-property-collector",
            {
              "stat": "Average",
              "period": 60,
              "label": "Collector Avg Duration",
              "color": "#1f77b4"
            }
          ],
          [
            "AWS/Lambda",
            "Duration",
            "FunctionName",
            "production-threshold-optimizer",
            {
              "stat": "Average",
              "period": 60,
              "label": "Optimizer Avg Duration",
              "color": "#ff7f0e"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "⏱️ Lambda Execution Duration (ms)",
        "period": 60,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Duration (ms)"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    },
    {
      "height": 6,
      "width": 12,
      "y": 12,
      "x": 12,
      "type": "metric",
      "properties": {
        "view": "timeSeries",
        "stacked": false,
        "metrics": [
          [
            "AWS/Lambda",
            "Errors",
            "FunctionName",
            "production-data-generator",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Data Generator Errors",
              "color": "#d62728"
            }
          ],
          [
            "AWS/Lambda",
            "Errors",
            "FunctionName",
            "production-property-collector",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Collector Errors",
              "color": "#ff7f0e"
            }
          ],
          [
            "AWS/Lambda",
            "Errors",
            "FunctionName",
            "production-property-processor",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Processor Errors",
              "color": "#9467bd"
            }
          ],
          [
            "AWS/Lambda",
            "Errors",
            "FunctionName",
            "production-threshold-optimizer",
            {
              "stat": "Sum",
              "period": 300,
              "label": "Optimizer Errors",
              "color": "#8c564b"
            }
          ]
        ],
        "region": "us-east-1",
        "title": "🚨 Lambda Errors",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0,
            "label": "Error Count"
          }
        },
        "legend": {
          "position": "bottom"
        }
      }
    }
  ]
}
```

---

## Setup Instructions

### Step 1: Open CloudWatch Console

Navigate to the AWS CloudWatch console at:
```
https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:
```

### Step 2: Create Each Dashboard

For each of the four dashboards:

1. Click **Create dashboard**
2. Enter the dashboard name exactly as shown:
   - `RealTimeSpikeMonitoring`
   - `Cost_Savings_Dashboard`
   - `ML_Dashboard`
   - `HousePriceMonitoring`
3. When prompted to add a widget, click **Cancel**
4. Click the **Actions** dropdown → **View/edit source**
5. Paste the corresponding JSON from this guide
6. Click **Update**
7. Click **Save dashboard**

### Step 3: Verify Metrics

After deploying the system and running a test batch, verify that metrics appear in your dashboards:

```bash
# Generate test data to populate metrics
aws lambda invoke \
    --function-name production-data-generator \
    --payload '{"count": 50}' \
    --region us-east-1 \
    response.json

# Wait 2-3 minutes for the pipeline to process, then check dashboards
```

### Custom Metric Namespace Reference

All custom metrics are published under the namespace `Custom/HousePriceML`. AWS built-in metrics use their standard namespaces:

| Namespace | Source | Metrics |
|-----------|--------|---------|
| `Custom/HousePriceML` | Property Processor, Threshold Optimizer | Model_Accuracy, Records_Processed, Cost_Savings_Scaled, etc. |
| `AWS/SQS` | Amazon SQS | ApproximateNumberOfMessagesVisible, NumberOfMessagesSent, etc. |
| `AWS/Lambda` | AWS Lambda | Invocations, Duration, Errors |
| `AWS/DynamoDB` | Amazon DynamoDB | ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits |

### AWS CLI Dashboard Creation

You can also create dashboards programmatically using the AWS CLI. Save each JSON block above to a file (e.g., `realtime-spike.json`) and run:

```bash
# Create RealTimeSpikeMonitoring dashboard
aws cloudwatch put-dashboard \
    --dashboard-name RealTimeSpikeMonitoring \
    --dashboard-body file://realtime-spike.json \
    --region us-east-1

# Create Cost_Savings_Dashboard
aws cloudwatch put-dashboard \
    --dashboard-name Cost_Savings_Dashboard \
    --dashboard-body file://cost-savings.json \
    --region us-east-1

# Create ML_Dashboard
aws cloudwatch put-dashboard \
    --dashboard-name ML_Dashboard \
    --dashboard-body file://ml-dashboard.json \
    --region us-east-1

# Create HousePriceMonitoring dashboard
aws cloudwatch put-dashboard \
    --dashboard-name HousePriceMonitoring \
    --dashboard-body file://house-price-monitoring.json \
    --region us-east-1
```

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|---------|
| No data in dashboards | Metrics not yet published | Run a test batch and wait 5 minutes |
| Missing custom metrics | Lambda not publishing to CloudWatch | Check Lambda logs for `put_metric_data` errors |
| AWS/SQS metrics missing | Queue name mismatch | Verify `property-stream-queue` exists in us-east-1 |
| DynamoDB metrics at zero | No read/write activity | Process a batch to generate DynamoDB operations |
| Gauge shows no value | Metric not yet emitted | Gauges need at least one data point; run the pipeline first |