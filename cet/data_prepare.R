library(optparse)
library(dplyr)
library(ggplot2)
library(RMySQL)
library(rredis)

option_list = list(
  make_option('--banker', action = 'store_true', default = FALSE)
)
opt = parse_args(OptionParser(option_list = option_list))

conn = dbConnect(MySQL(), group='cet')
banker_conn = dbConnect(MySQL(), group='banker_read')
redis_banker = list(host = 'shakuras', port = 6301)
redis_cet = list(host = 'shakuras', port = 6303)

if (opt$banker) {
  conn = banker_conn
  redisConnect(host = redis_banker$host, port = redis_banker$port)
} else {
  redisConnect(host = redis_cet$host, port = redis_cet$port)
}

EXAM_KIND_CET4 = 1L
EXAM_KIND_CET6 = 2L

load_qfactor <- function(exam_kind) {

  qfactor_info <- function(key) {
    qtype = as.integer(tail(unlist(strsplit(key, '/')), 1))
    qid = as.integer(unlist(redisLRange(key, 0, -1)))
    data.frame(qtype = qtype, qid = qid, exam_kind = exam_kind)
  }

  QUESTION_INV_INDEX_PATTERN = '/alg/english/question_index/%s/*'
  keys = redisKeys(sprintf(QUESTION_INV_INDEX_PATTERN, exam_kind))
  return(bind_rows(lapply(keys, qfactor_info)))
}

get_question_factor <- function() {
  cet4_df = load_qfactor(EXAM_KIND_CET4)
  cet6_df = load_qfactor(EXAM_KIND_CET6)
  return(bind_rows(cet4_df, cet6_df))
}

#针对大题的过滤
#去掉单题时间特别长和特别短的。
get_valid_question <- function(qfactor) {
    A = dbGetQuery(conn, 'select target_kind, target_id, user_id,
                   datetime, seconds, question_type, app_question_kind
                   from question_record')
    #A = read.table('data/question_record.csv', sep='\t',
                   #stringsAsFactors=F)
    names(A) = c('qtype', 'qid', 'uid', 'datetime', 'seconds',
                 'record_type', 'app_qkind')
    A = inner_join(A, qfactor)

    A %>%
        filter(seconds < 1800) %>%
        filter(app_qkind != 100 | seconds >= 40) %>%
        filter(app_qkind != 103 | seconds >= 10) %>%
        mutate(date = as.Date(strptime(datetime, "%F %T"))) %>%
        select(qtype, qid, uid, date) -> B
    return(B)
}

get_question_record <- function(qvalid) {
    A = dbGetQuery(conn, 'select question_type, question_id,
                   parent_kind, parent_id, user_id, status, date
                   from question_record_detail')
    #A = read.table('data/question_record_detail.csv', sep='\t',
                   #stringsAsFactors = F)
    names(A) = c('subtype', 'subid', 'qtype', 'qid', 'uid',
                 'status', 'date')
    A$date = as.Date(A$date)
    A = inner_join(A, qvalid)
    return(A)
}

#过滤做题特别少的人
user_filter <- function(record) {
    record %>%
        group_by(uid) %>%
        summarise(count=n()) %>%
        filter(count >= 10) -> S
    return(semi_join(record, S))
}

#获取题目难度
get_question_difficulty <- function() {
    context = dbGetQuery(banker_conn, 'select question_type, id, difficulty
                         from context_choice_question')
    names(context) = c('subtype', 'subid', 'difficulty')
    listen = dbGetQuery(banker_conn, 'select question_type, id, difficulty
                        from listen_choice_question')
    names(listen) = c('subtype', 'subid', 'difficulty')
    diff = rbind(context, listen)
    return(diff)
}


main <- function(outpath) {
    qfactor = get_question_factor()
    qvalid = get_valid_question(qfactor)
    record = get_question_record(qvalid)
    record = user_filter(record)
    record = filter(record, status != 0)
    diff = get_question_difficulty()
    record = inner_join(record, diff)
    write.table(record, outpath, sep='\t', quote=F, row.name=F, col.names=F)
}

if (opt$banker) {
  outpath = '/home/shenfei/data/dagobah/banker_cet_question_record.csv'
} else {
  outpath = '/home/shenfei/data/dagobah/cet_question_record.csv'
}
main(outpath)

