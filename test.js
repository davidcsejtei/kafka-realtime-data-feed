const { Kafka } = require('kafkajs')

const kafka = new Kafka({
  clientId: 'test-client',
  brokers: ['localhost:9092']
})

const topic = 'rocket-telemetry'

async function testKafka() {
  const producer = kafka.producer()
  const consumer = kafka.consumer({ groupId: 'test-group' })

  await producer.connect()
  await consumer.connect()

  await consumer.subscribe({ topic, fromBeginning: true })

  consumer.run({
    eachMessage: async ({ message }) => {
      console.log(`📥 Üzenet érkezett: ${message.value.toString()}`)
    }
  })

  await producer.send({
    topic,
    messages: [{ value: 'Teszt üzenet ' + new Date().toISOString() }]
  })

  console.log('✅ Teszt üzenet elküldve.')
}

testKafka().catch(console.error)
